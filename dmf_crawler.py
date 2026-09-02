import urllib.request
import urllib.parse
import ssl
import json
import re
from bs4 import BeautifulSoup

class DMFCrawler:
    BASE_URL = 'https://nedrug.mfds.go.kr/pbp/CCBAC03/getList'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    def __init__(self):
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def fetch_dmf_list(self, ingredient="", reg_no="", applicant="", page=1, limit=10):
        """
        Fetch DMF list from nedrug.mfds.go.kr with given filters.
        """
        params = {
            'page': str(page),
            'limit': str(limit),
            'searchIngrKorName': ingredient,
            'searchDmfPermitNo': reg_no,
            'searchItem': applicant
        }

        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self.HEADERS)
        
        try:
            with urllib.request.urlopen(req, context=self.ctx) as response:
                html = response.read().decode('utf-8')
        except Exception as e:
            return {'success': False, 'error': str(e), 'items': []}

        soup = BeautifulSoup(html, 'html.parser')
        items = []

        # Find main table
        table = soup.find('table')
        if not table:
            return {'success': True, 'count': 0, 'items': []}

        tbody = table.find('tbody')
        rows = tbody.find_all('tr') if tbody else table.find_all('tr')[1:]

        for row in rows:
            tds = row.find_all('td')
            # Main desktop row has 18 columns
            if len(tds) >= 17:
                raw_texts = [td.get_text(" ", strip=True) for td in tds]
                
                # Helper to strip prefix like "등록번호 ", "성분명 "
                def clean_prefix(val, prefixes):
                    for p in prefixes:
                        if val.startswith(p):
                            return val[len(p):].strip()
                    return val.strip()

                reg_no_val = clean_prefix(raw_texts[2], ['등록번호'])
                ingredient_val = clean_prefix(raw_texts[3], ['성분명'])
                applicant_val = clean_prefix(raw_texts[4], ['신청인'])
                mfr_val = clean_prefix(raw_texts[5], ['제조소명'])
                address_val = clean_prefix(raw_texts[7], ['제조소소재지'])
                country_val = clean_prefix(raw_texts[9], ['제조국가'])
                first_reg_val = clean_prefix(raw_texts[11], ['최초등록일자'])
                last_change_val = clean_prefix(raw_texts[12], ['최종변경일자'])
                annual_year_val = clean_prefix(raw_texts[13], ['최종연차보고년도'])
                status_val = clean_prefix(raw_texts[14], ['취소/취하구분'])
                cancel_date_val = clean_prefix(raw_texts[15], ['취소/취하일자'])
                doc_no_val = clean_prefix(raw_texts[16], ['문서번호'])
                linked_doc_val = clean_prefix(raw_texts[17], ['연계심사문서번호']) if len(raw_texts) > 17 else ""

                item = {
                    'seq': raw_texts[0],
                    'reg_no': reg_no_val,
                    'ingredient': ingredient_val,
                    'applicant': applicant_val,
                    'manufacturer': mfr_val,
                    'address': address_val,
                    'country': country_val,
                    'first_reg_date': first_reg_val,
                    'last_change_date': last_change_val,
                    'annual_report_year': annual_year_val,
                    'status': status_val,
                    'cancel_date': cancel_date_val,
                    'doc_no': doc_no_val,
                    'linked_doc_no': linked_doc_val
                }
                items.append(item)

        return {
            'success': True,
            'count': len(items),
            'page': page,
            'query': {'ingredient': ingredient, 'reg_no': reg_no, 'applicant': applicant},
            'items': items
        }

if __name__ == '__main__':
    crawler = DMFCrawler()
    
    print("=== Testing Search: 성분명 '피나스테리드' ===")
    res1 = crawler.fetch_dmf_list(ingredient='피나스테리드', limit=5)
    print(json.dumps(res1, ensure_ascii=False, indent=2))
    
    print("\n=== Testing Search: 등록번호 '20250623-94-E-188-16(A)' ===")
    res2 = crawler.fetch_dmf_list(reg_no='20250623-94-E-188-16(A)')
    print(json.dumps(res2, ensure_ascii=False, indent=2))
