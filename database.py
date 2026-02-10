import sqlite3
import datetime
import os

class Storage:
    def __init__(self, db_path="known_places.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
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
        conn.commit()
        conn.close()

    def get_count(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM places')
        count = cursor.fetchone()[0]
        conn.close()
        return count

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
