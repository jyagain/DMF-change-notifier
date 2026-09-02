import os
import sys
import json
from datetime import datetime
from dmf_crawler import DMFCrawler

sys.stdout.reconfigure(encoding='utf-8')

SNAPSHOT_FILE = 'dmf_snapshot.json'

class DMFMonitor:
    def __init__(self):
        self.crawler = DMFCrawler()
        self.snapshot = self.load_snapshot()

    def load_snapshot(self):
        if os.path.exists(SNAPSHOT_FILE):
            try:
                with open(SNAPSHOT_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Warning] Failed to load snapshot: {e}")
        return {}

    def save_snapshot(self):
        with open(SNAPSHOT_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.snapshot, f, ensure_ascii=False, indent=2)

    def check_updates(self, target_reg_numbers):
        """
        Check updates for a list of DMF registration numbers (등록번호).
        Returns detected changes.
        """
        detected_changes = []
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitoring {len(target_reg_numbers)} registered items...")

        for reg_no in target_reg_numbers:
            res = self.crawler.fetch_dmf_list(reg_no=reg_no)
            if not res['success'] or not res['items']:
                print(f"[Warning] Item {reg_no} not found or query failed.")
                continue

            current_item = res['items'][0]
            current_doc_no = current_item['doc_no']
            current_last_change = current_item['last_change_date']

            previous_data = self.snapshot.get(reg_no)

            if previous_data is None:
                # First time watching this item
                print(f"  [NEW TRACKING] Registered {reg_no} ({current_item['ingredient']}) -> Doc No: '{current_doc_no}'")
                self.snapshot[reg_no] = {
                    'reg_no': reg_no,
                    'ingredient': current_item['ingredient'],
                    'applicant': current_item['applicant'],
                    'manufacturer': current_item['manufacturer'],
                    'doc_no': current_doc_no,
                    'last_change_date': current_last_change,
                    'last_checked': datetime.now().isoformat()
                }
            else:
                prev_doc_no = previous_data.get('doc_no', '')
                if prev_doc_no != current_doc_no:
                    # CHANGE DETECTED!
                    change_event = {
                        'reg_no': reg_no,
                        'ingredient': current_item['ingredient'],
                        'applicant': current_item['applicant'],
                        'manufacturer': current_item['manufacturer'],
                        'old_doc_no': prev_doc_no,
                        'new_doc_no': current_doc_no,
                        'old_change_date': previous_data.get('last_change_date', ''),
                        'new_change_date': current_last_change,
                        'timestamp': datetime.now().isoformat()
                    }
                    detected_changes.append(change_event)
                    print(f"  [🚨 CHANGE DETECTED!] {reg_no}: '{prev_doc_no}' => '{current_doc_no}'")

                    # Update snapshot
                    previous_data['doc_no'] = current_doc_no
                    previous_data['last_change_date'] = current_last_change
                    previous_data['last_checked'] = datetime.now().isoformat()
                else:
                    print(f"  [OK] {reg_no} ({current_item['ingredient']}) -> No change (Doc No: '{current_doc_no}')")
                    previous_data['last_checked'] = datetime.now().isoformat()

        self.save_snapshot()
        return detected_changes

    def send_simulated_notifications(self, changes, user_email="user@example.com", user_phone="010-1234-5678"):
        """
        Simulate sending Email and SMS notification for detected changes.
        """
        if not changes:
            return

        print("\n" + "="*50)
        print(f"📧 [NOTIFICATION SIMULATOR] Sending alerts to {user_email} & {user_phone}")
        print("="*50)

        for c in changes:
            email_body = f"""
[DMF 문서번호 변경 알림]
------------------------------------
• 성분명: {c['ingredient']}
• 등록번호: {c['reg_no']}
• 신청인: {c['applicant']}
• 제조소: {c['manufacturer']}
------------------------------------
• 기존 문서번호: {c['old_doc_no']}
• ⚡ 변경 문서번호: {c['new_doc_no']}
• 변경일자: {c['new_change_date']}
------------------------------------
의약품안전나라 nedrug.mfds.go.kr에서 확인하세요.
"""
            sms_text = f"[DMF알림] {c['ingredient']}({c['reg_no']}) 문서번호가 '{c['old_doc_no']}'에서 '{c['new_doc_no']}'(으)로 변경되었습니다."

            print("--- EMAIL MESSAGE ---")
            print(email_body.strip())
            print("--- SMS MESSAGE ---")
            print(sms_text)
            print("-" * 50)

if __name__ == '__main__':
    monitor = DMFMonitor()
    
    # Example target items to watch
    target_items = [
        "20250623-94-E-188-16(A)", # 피나스테리드 (리더스바이오)
        "20250519-94-E-187-15(A)", # 피나스테리드 (오트란코리아)
        "20251010-94-E-193-18"      # 피나스테리드 (대웅바이오)
    ]
    
    print("--- 1ST CHECK (Initialize Snapshot) ---")
    changes1 = monitor.check_updates(target_items)
    
    # Simulate a version bump change in snapshot to test change detection
    print("\n--- SIMULATING DOCUMENT NUMBER CHANGE FOR TEST ---")
    if "20250519-94-E-187-15(A)" in monitor.snapshot:
        monitor.snapshot["20250519-94-E-187-15(A)"]["doc_no"] = "v0.0.0/2026"
    
    print("\n--- 2ND CHECK (Detect Change & Alert) ---")
    changes2 = monitor.check_updates(target_items)
    monitor.send_simulated_notifications(changes2)
