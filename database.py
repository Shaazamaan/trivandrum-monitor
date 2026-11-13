import sqlite3
import datetime
import os

class Storage:
    def __init__(self, db_path="known_places.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        # WAL mode removed for Git-Repo stability (avoiding .shm/.wal sync issues)
        # conn.execute('PRAGMA journal_mode=WAL;') 
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS places (
                place_id TEXT PRIMARY KEY,
                name TEXT,
                address TEXT,
                category TEXT,
                phone TEXT,
                website TEXT,
                discovered_at TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scans (
                combo TEXT PRIMARY KEY,
                first_scanned_at TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def is_baselined(self, keyword, location):
        conn = sqlite3.connect(self.db_path)
        row = conn.execute('SELECT 1 FROM scans WHERE combo = ?', (f"v2|{keyword}|{location}".lower(),)).fetchone()
        conn.close()
        return row is not None

    def mark_baselined(self, keyword, location):
        conn = sqlite3.connect(self.db_path)
        conn.execute('INSERT OR IGNORE INTO scans (combo, first_scanned_at) VALUES (?, ?)',
                     (f"v2|{keyword}|{location}".lower(), datetime.datetime.now()))
        conn.commit()
        conn.close()

    def get_state(self, key, default=0):
        conn = sqlite3.connect(self.db_path)
        conn.execute('CREATE TABLE IF NOT EXISTS state (k TEXT PRIMARY KEY, v INTEGER)')
        row = conn.execute('SELECT v FROM state WHERE k = ?', (key,)).fetchone()
        conn.close()
        return row[0] if row else default

    def set_state(self, key, value):
        conn = sqlite3.connect(self.db_path)
        conn.execute('CREATE TABLE IF NOT EXISTS state (k TEXT PRIMARY KEY, v INTEGER)')
        conn.execute('INSERT OR REPLACE INTO state (k, v) VALUES (?, ?)', (key, value))
        conn.commit()
        conn.close()

    def get_count(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM places')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def export_partitioned(self):
        """
        Exports two files:
        1. data.json: Latest 1000 items (Hot Data for fast loading)
        2. archive.json: All items (Cold Data for history)
        """
        import json
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Fetch ALL data sorted by newest first
        cursor.execute('SELECT * FROM places ORDER BY discovered_at DESC')
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Convert timestamps
        for row in rows:
            if row.get('discovered_at'):
                row['discovered_at'] = str(row['discovered_at'])

        # 1. HOT DATA (Latest 1000)
        hot_data = rows[:1000]
        with open("data.json", 'w', encoding='utf-8') as f:
            json.dump(hot_data, f, indent=2, ensure_ascii=False)
            
        # 2. COLD DATA (Full Archive) - Only if we have more than 1000
        if len(rows) > 0:
            with open("archive.json", 'w', encoding='utf-8') as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)
                
        print(f"Exported: data.json ({len(hot_data)}), archive.json ({len(rows)})")

    def is_new(self, place_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM places WHERE place_id = ?', (place_id,))
        exists = cursor.fetchone()
        conn.close()
        return not exists

    def add_place(self, place_data):
        """
        place_data should be a dict with keys:
        place_id, name, address, category, phone, website
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO places 
                (place_id, name, address, category, phone, website, discovered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                place_data.get('place_id'),
                place_data.get('name'),
                place_data.get('address'),
                place_data.get('category'),
                place_data.get('phone'),
                place_data.get('website'),
                datetime.datetime.now()
            ))
            conn.commit()
        except Exception as e:
            print(f"Error adding place to DB: {e}")
        finally:
            conn.close()
