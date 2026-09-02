import sys
import urllib.request
import urllib.parse
import ssl
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://nedrug.mfds.go.kr/pbp/CCBAC03'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, context=ctx) as response:
    html = response.read().decode('utf-8')

soup = BeautifulSoup(html, 'html.parser')
forms = soup.find_all('form')
print(f"Total forms found: {len(forms)}")

for i, form in enumerate(forms):
    action = form.get('action')
    method = form.get('method', 'GET')
    form_id = form.get('id')
    print(f"\n--- Form #{i+1} [ID: {form_id}, Action: {action}, Method: {method}] ---")
    inputs = form.find_all(['input', 'select'])
    for inp in inputs:
        inp_type = inp.get('type', inp.name)
        inp_name = inp.get('name')
        inp_val = inp.get('value', '')
        if inp_name:
            print(f"  - {inp_name} ({inp_type}) = '{inp_val}'")
