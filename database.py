import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'dmf_notifier.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Table 1: Watchlist items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reg_no TEXT UNIQUE NOT NULL,
                ingredient TEXT,
                applicant TEXT,
                manufacturer TEXT,
                first_reg_date TEXT,
                doc_no TEXT,
                last_change_date TEXT,
                status TEXT DEFAULT '정상',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table 2: Change logs & notification timeline
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reg_no TEXT NOT NULL,
                ingredient TEXT,
                applicant TEXT,
                old_doc_no TEXT,
                new_doc_no TEXT,
                old_change_date TEXT,
                new_change_date TEXT,
                notified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table 3: User settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Insert default settings if empty
        default_settings = {
            'email_enabled': 'true',
            'email_recipient': 'user@example.com',
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': '587',
            'smtp_user': '',
            'smtp_password': '',
            'sms_enabled': 'true',
            'sms_phone': '010-1234-5678',
            'solapi_api_key': '',
            'solapi_api_secret': '',
            'solapi_sender': '',
            'check_interval_minutes': '60'
        }

        for k, v in default_settings.items():
            cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (k, v))
            
        conn.commit()

# Helper Functions
def add_to_watchlist(item_dict):
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO watchlist (reg_no, ingredient, applicant, manufacturer, first_reg_date, doc_no, last_change_date, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(reg_no) DO UPDATE SET
                doc_no=excluded.doc_no,
                last_change_date=excluded.last_change_date,
                updated_at=excluded.updated_at
        ''', (
            item_dict.get('reg_no'),
            item_dict.get('ingredient'),
            item_dict.get('applicant'),
            item_dict.get('manufacturer'),
            item_dict.get('first_reg_date'),
            item_dict.get('doc_no'),
            item_dict.get('last_change_date'),
            item_dict.get('status', '정상'),
            now, now
        ))
        conn.commit()

def remove_from_watchlist(reg_no):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM watchlist WHERE reg_no = ?', (reg_no,))
        conn.commit()

def get_watchlist():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM watchlist ORDER BY created_at DESC')
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def update_watchlist_item(reg_no, new_doc_no, new_change_date):
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE watchlist
            SET doc_no = ?, last_change_date = ?, updated_at = ?
            WHERE reg_no = ?
        ''', (new_doc_no, new_change_date, now, reg_no))
        conn.commit()

def log_change_event(reg_no, ingredient, applicant, old_doc_no, new_doc_no, old_change_date, new_change_date, notified=1):
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO logs (reg_no, ingredient, applicant, old_doc_no, new_doc_no, old_change_date, new_change_date, notified, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (reg_no, ingredient, applicant, old_doc_no, new_doc_no, old_change_date, new_change_date, notified, now))
        conn.commit()

def get_change_logs(limit=50):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM logs ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_settings():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM settings')
        rows = cursor.fetchall()
        return {r['key']: r['value'] for r in rows}

def save_settings(settings_dict):
    with get_db() as conn:
        cursor = conn.cursor()
        for k, v in settings_dict.items():
            cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (k, str(v)))
        conn.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
