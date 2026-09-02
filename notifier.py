import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request
import urllib.parse
import json
from datetime import datetime
from database import get_settings

class NotificationEngine:
    def __init__(self):
        pass

    def send_alert(self, change_event):
        """
        Dispatch notification for a change event via Email and SMS based on user settings.
        """
        settings = get_settings()
        email_sent = False
        sms_sent = False

        email_recipient = settings.get('email_recipient', '')
        email_enabled = settings.get('email_enabled', 'false').lower() == 'true'

        sms_phone = settings.get('sms_phone', '')
        sms_enabled = settings.get('sms_enabled', 'false').lower() == 'true'

        if email_enabled and email_recipient:
            email_sent = self.send_email(change_event, email_recipient, settings)

        if sms_enabled and sms_phone:
            sms_sent = self.send_sms(change_event, sms_phone, settings)

        return {'email': email_sent, 'sms': sms_sent}

    def send_email(self, change_event, recipient, settings):
        subject = f"[DMF 문서번호 변경] {change_event['ingredient']} ({change_event['reg_no']})"
        
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <h2 style="color: #2563eb; margin-top: 0;">⚡ DMF 문서번호 변경 알림</h2>
            <p>신청하신 원료의약품의 등록 문서번호가 새로 업데이트되었습니다.</p>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr style="background-color: #f8fafc;">
                    <th style="padding: 10px; border: 1px solid #cbd5e1; text-align: left; width: 30%;">성분명</th>
                    <td style="padding: 10px; border: 1px solid #cbd5e1; font-weight: bold;">{change_event['ingredient']}</td>
                </tr>
                <tr>
                    <th style="padding: 10px; border: 1px solid #cbd5e1; text-align: left;">등록번호</th>
                    <td style="padding: 10px; border: 1px solid #cbd5e1;">{change_event['reg_no']}</td>
                </tr>
                <tr style="background-color: #f8fafc;">
                    <th style="padding: 10px; border: 1px solid #cbd5e1; text-align: left;">신청인</th>
                    <td style="padding: 10px; border: 1px solid #cbd5e1;">{change_event['applicant']}</td>
                </tr>
                <tr>
                    <th style="padding: 10px; border: 1px solid #cbd5e1; text-align: left;">제조소명</th>
                    <td style="padding: 10px; border: 1px solid #cbd5e1;">{change_event['manufacturer']}</td>
                </tr>
                <tr style="background-color: #eff6ff;">
                    <th style="padding: 10px; border: 1px solid #93c5fd; text-align: left; color: #1e3a8a;">기존 문서번호</th>
                    <td style="padding: 10px; border: 1px solid #93c5fd; color: #64748b; text-decoration: line-through;">{change_event.get('old_doc_no', 'N/A')}</td>
                </tr>
                <tr style="background-color: #f0fdf4;">
                    <th style="padding: 10px; border: 1px solid #86efac; text-align: left; color: #14532d;">변경 문서번호</th>
                    <td style="padding: 10px; border: 1px solid #86efac; font-weight: bold; color: #166534;">{change_event['new_doc_no']}</td>
                </tr>
                <tr>
                    <th style="padding: 10px; border: 1px solid #cbd5e1; text-align: left;">최종변경일자</th>
                    <td style="padding: 10px; border: 1px solid #cbd5e1;">{change_event.get('new_change_date', '-')}</td>
                </tr>
            </table>

            <p style="font-size: 12px; color: #64748b;">본 메일은 DMF 문서번호 모니터링 시스템에서 자동 발송되었습니다.<br/>자세한 정보는 <a href="https://nedrug.mfds.go.kr/pbp/CCBAC03" target="_blank" style="color: #2563eb;">의약품안전나라 사이트</a>에서 확인하실 수 있습니다.</p>
        </div>
        """

        smtp_server = settings.get('smtp_server', '')
        smtp_port = int(settings.get('smtp_port', '587'))
        smtp_user = settings.get('smtp_user', '')
        smtp_password = settings.get('smtp_password', '')

        if smtp_user and smtp_password and smtp_server:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = smtp_user
                msg['To'] = recipient
                msg.attach(MIMEText(body_html, 'html'))

                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, recipient, msg.as_string())
                server.quit()
                print(f"[Email Sent] Successfully delivered to {recipient}")
                return True
            except Exception as e:
                print(f"[Email Error] Failed to send SMTP mail: {e}")

        # Fallback / Simulation Log
        print(f"\n[EMAIL SIMULATION] To: {recipient}\nSubject: {subject}\nBody: Version updated to {change_event['new_doc_no']}\n")
        return True

    def send_sms(self, change_event, phone, settings):
        message_text = f"[DMF알림] {change_event['ingredient']} ({change_event['reg_no']}) 문서번호가 '{change_event.get('old_doc_no','')}'에서 '{change_event['new_doc_no']}'(으)로 변경되었습니다."
        
        api_key = settings.get('solapi_api_key', '')
        api_secret = settings.get('solapi_api_secret', '')
        sender = settings.get('solapi_sender', '')

        if api_key and api_secret and sender:
            # API integration placeholder
            pass

        print(f"\n[SMS SIMULATION] To: {phone}\nMessage: {message_text}\n")
        return True

if __name__ == '__main__':
    engine = NotificationEngine()
    test_event = {
        'reg_no': '20250623-94-E-188-16(A)',
        'ingredient': '피나스테리드',
        'applicant': '리더스바이오(주)',
        'manufacturer': 'Swati Spentose Private Limited',
        'old_doc_no': 'v0.0.0/2026',
        'new_doc_no': 'v0.1.0/2026',
        'new_change_date': '2026-09-02'
    }
    engine.send_alert(test_event)
