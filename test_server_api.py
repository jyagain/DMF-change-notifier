import urllib.request
import urllib.parse
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'http://127.0.0.1:8000'

def test_api():
    print("=== Testing FastAPI Server Endpoints ===")
    
    # 1. Root / static index.html test
    req = urllib.request.Request(f"{BASE_URL}/")
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8')
        assert "DMF" in html
        print("✅ Root GET '/' returned 200 HTML page.")

    # 2. Watchlist GET test
    req = urllib.request.Request(f"{BASE_URL}/api/watchlist")
    with urllib.request.urlopen(req) as resp:
        watchlist = json.loads(resp.read().decode('utf-8'))
        print(f"✅ GET '/api/watchlist' returned {len(watchlist)} items.")

    # 3. Search API test
    params = urllib.parse.urlencode({'ingredient': '피나스테리드'})
    req = urllib.request.Request(f"{BASE_URL}/api/search?{params}")
    with urllib.request.urlopen(req) as resp:
        search_res = json.loads(resp.read().decode('utf-8'))
        assert search_res['success'] is True
        print(f"✅ GET '/api/search' returned {search_res['count']} search items from nedrug.mfds.go.kr.")
        first_item = search_res['items'][0] if search_res['items'] else None

    # 4. Add item to Watchlist POST test
    if first_item:
        data = json.dumps(first_item).encode('utf-8')
        req = urllib.request.Request(f"{BASE_URL}/api/watchlist", data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as resp:
            add_res = json.loads(resp.read().decode('utf-8'))
            assert add_res['success'] is True
            print(f"✅ POST '/api/watchlist' added item '{first_item['reg_no']}' to watchlist.")

    # 5. Check Now POST test
    req = urllib.request.Request(f"{BASE_URL}/api/check-now", data=b'{}', headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        check_res = json.loads(resp.read().decode('utf-8'))
        assert check_res['success'] is True
        print(f"✅ POST '/api/check-now' checked all watched items.")

    # 6. Test Notify POST test
    req = urllib.request.Request(f"{BASE_URL}/api/test-notify", data=b'{}', headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        notify_res = json.loads(resp.read().decode('utf-8'))
        assert notify_res['success'] is True
        print(f"✅ POST '/api/test-notify' delivered test notification.")

    print("\n🎉 ALL API ENDPOINTS VERIFIED SUCCESSFULLY!")

if __name__ == '__main__':
    time.sleep(2)
    test_api()
