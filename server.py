import asyncio
import os
import sys
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

from database import (
    init_db, add_to_watchlist, remove_from_watchlist, get_watchlist,
    update_watchlist_item, log_change_event, get_change_logs,
    get_settings, save_settings
)
from dmf_crawler import DMFCrawler
from notifier import NotificationEngine

# Set stdout UTF-8 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

app = FastAPI(title="DMF Document Number Notification Service", version="1.0.0")

# Mount static files directory
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

crawler = DMFCrawler()
notifier = NotificationEngine()

# Initialize DB on start
@app.on_event("startup")
async def startup_event():
    init_db()
    # Start background scheduler loop
    asyncio.create_task(background_checker_loop())

async def run_check_cycle():
    """
    Check current DMF state for all monitored items in watchlist.
    Returns list of detected changes.
    """
    watchlist = get_watchlist()
    detected_changes = []
    
    for item in watchlist:
        reg_no = item['reg_no']
        res = crawler.fetch_dmf_list(reg_no=reg_no)
        if res['success'] and res['items']:
            current_item = res['items'][0]
            curr_doc_no = current_item['doc_no']
            curr_change_date = current_item['last_change_date']

            old_doc_no = item['doc_no']
            old_change_date = item['last_change_date']

            # If document number changed (or date updated)
            if old_doc_no and old_doc_no != curr_doc_no:
                change_event = {
                    'reg_no': reg_no,
                    'ingredient': current_item['ingredient'],
                    'applicant': current_item['applicant'],
                    'manufacturer': current_item['manufacturer'],
                    'old_doc_no': old_doc_no,
                    'new_doc_no': curr_doc_no,
                    'old_change_date': old_change_date,
                    'new_change_date': curr_change_date,
                    'timestamp': datetime.now().isoformat()
                }
                detected_changes.append(change_event)
                
                # Update watchlist in DB
                update_watchlist_item(reg_no, curr_doc_no, curr_change_date)
                
                # Log change event in DB
                log_change_event(
                    reg_no=reg_no,
                    ingredient=current_item['ingredient'],
                    applicant=current_item['applicant'],
                    old_doc_no=old_doc_no,
                    new_doc_no=curr_doc_no,
                    old_change_date=old_change_date,
                    new_change_date=curr_change_date
                )
                
                # Send Notifications
                notifier.send_alert(change_event)
            else:
                # Update last checked timestamp
                update_watchlist_item(reg_no, curr_doc_no, curr_change_date)
                
    return detected_changes

async def background_checker_loop():
    """
    Periodic background task checking DMF document numbers.
    """
    while True:
        try:
            settings = get_settings()
            interval_min = int(settings.get('check_interval_minutes', '60'))
            interval_sec = max(60, interval_min * 60)  # Min 60 sec
        except Exception:
            interval_sec = 3600

        await asyncio.sleep(interval_sec)
        try:
            await run_check_cycle()
        except Exception as e:
            print(f"[Scheduler Error] {e}")

# API Models
class WatchitemRequest(BaseModel):
    reg_no: str
    ingredient: str
    applicant: str
    manufacturer: str
    first_reg_date: Optional[str] = ""
    doc_no: Optional[str] = ""
    last_change_date: Optional[str] = ""
    status: Optional[str] = "정상"

class SettingsRequest(BaseModel):
    email_enabled: Optional[str] = "false"
    email_recipient: Optional[str] = ""
    smtp_server: Optional[str] = ""
    smtp_port: Optional[str] = "587"
    smtp_user: Optional[str] = ""
    smtp_password: Optional[str] = ""
    sms_enabled: Optional[str] = "false"
    sms_phone: Optional[str] = ""
    solapi_api_key: Optional[str] = ""
    solapi_api_secret: Optional[str] = ""
    solapi_sender: Optional[str] = ""
    check_interval_minutes: Optional[str] = "60"

# Routes
@app.get("/")
async def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "DMF Notification Server is running."}

@app.get("/api/search")
async def search_dmf(
    ingredient: str = Query("", description="성분명"),
    reg_no: str = Query("", description="등록번호"),
    applicant: str = Query("", description="신청인"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Search DMF records live from nedrug.mfds.go.kr
    """
    res = crawler.fetch_dmf_list(
        ingredient=ingredient,
        reg_no=reg_no,
        applicant=applicant,
        page=page,
        limit=limit
    )
    return res

@app.get("/api/watchlist")
async def list_watchlist():
    return get_watchlist()

@app.post("/api/watchlist")
async def add_watchlist(item: WatchitemRequest):
    add_to_watchlist(item.dict())
    return {"success": True, "message": f"Successfully added {item.reg_no} ({item.ingredient}) to watchlist."}

@app.delete("/api/watchlist/{reg_no:path}")
async def delete_watchlist(reg_no: str):
    remove_from_watchlist(reg_no)
    return {"success": True, "message": f"Removed {reg_no} from watchlist."}

@app.post("/api/check-now")
async def trigger_check_now():
    """
    Trigger immediate check across all monitored items.
    """
    changes = await run_check_cycle()
    return {
        "success": True,
        "checked_at": datetime.now().isoformat(),
        "changes_detected": len(changes),
        "changes": changes
    }

@app.get("/api/logs")
async def list_logs():
    return get_change_logs()

@app.get("/api/settings")
async def get_user_settings():
    return get_settings()

@app.post("/api/settings")
async def update_user_settings(data: SettingsRequest):
    save_settings(data.dict())
    return {"success": True, "message": "Settings saved successfully."}

@app.post("/api/test-notify")
async def send_test_notification():
    test_event = {
        'reg_no': '20250623-94-E-188-16(A)',
        'ingredient': '피나스테리드 (테스트)',
        'applicant': '테스트제약(주)',
        'manufacturer': 'Test Pharma Pvt. Ltd.',
        'old_doc_no': 'v0.0.0/2026',
        'new_doc_no': 'v0.1.0/2026 (테스트)',
        'new_change_date': datetime.now().strftime('%Y-%m-%d')
    }
    res = notifier.send_alert(test_event)
    return {"success": True, "delivery": res, "message": "Test notification sent successfully."}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
