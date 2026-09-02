import sys
import urllib.request
import urllib.parse
import ssl
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base_url = 'https://nedrug.mfds.go.kr/pbp/CCBAC03/getList'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

params = {
    'page': '1',
    'limit': '10',
    'searchIngrKorName': '피나스테리드'
}

url = f"{base_url}?{urllib.parse.urlencode(params)}"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, context=ctx) as response:
    html = response.read().decode('utf-8')

soup = BeautifulSoup(html, 'html.parser')

# Let's check table or list items
table = soup.find('table')
if table:
    tbody = table.find('tbody')
    rows = tbody.find_all('tr') if tbody else table.find_all('tr')[1:]
    print(f"Total rows in tbody: {len(rows)}")
    
    for r_idx, r in enumerate(rows[:3]):
        print(f"\n================ ROW {r_idx+1} ================")
        tds = r.find_all('td')
        print(f"TD count: {len(tds)}")
        for c_idx, td in enumerate(tds):
            # Print clean text
            text = td.get_text(" ", strip=True)
            print(f"  Col {c_idx} (class={td.get('class')}): '{text}'")
