import sqlite3
import datetime

"""
Table: Cache
| id | hash_str(index) | expiry_time | path | created_at | updated_at | deleted_at | result |
"""


class CacheDB:
    """
    CacheDB is a wrapper for sqlite3
    """

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for index, col in enumerate(cursor.description):
            d[col[0]] = row[index]
        return d

    def __init__(self, db_path: str = './cache.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = self.dict_factory
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_str TEXT NOT NULL UNIQUE,
            expiry_time TIMESTAMP NOT NULL,
            path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP DEFAULT NULL,
            result TEXT DEFAULT "{}"
        );
        ''')
        self.conn.commit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.conn.close()

    def commit(self):
        self.conn.commit()

    def insert(self, hash_str: str, expiry_time: int, path: str, result: str, auto_commit: bool = True):
        self.cursor.execute('''
        INSERT INTO Cache (hash_str, expiry_time, path, result)
        VALUES (?, ?, ?, ?)
        ''', (hash_str, expiry_time, path, result))
        if auto_commit:
            self.conn.commit()

    def update(self, hash_str: str, expiry_time: int, path: str, created_at: int, updated_at: int,
               deleted_at: int | None, result: str, auto_commit: bool = True):
        # convert to timestamp
        if isinstance(expiry_time, int):
            expiry_time = datetime.datetime.utcfromtimestamp(expiry_time)
        if isinstance(created_at, int):
            created_at = datetime.datetime.utcfromtimestamp(created_at)
        if isinstance(updated_at, int):
            updated_at = datetime.datetime.utcfromtimestamp(updated_at)

        self.cursor.execute('''
        UPDATE Cache
        SET expiry_time = ?, path = ?, created_at = ?, updated_at = ?, deleted_at = ?, result = ?
        WHERE hash_str = ?
        ''', (expiry_time, path, created_at, updated_at, deleted_at, result, hash_str))
        if auto_commit:
            self.conn.commit()

    def delete(self, hash_str: str, auto_commit: bool = True):
        self.cursor.execute('''
        UPDATE Cache
        SET deleted_at = CURRENT_TIMESTAMP
        WHERE hash_str = ?
        ''', (hash_str,))
        if auto_commit:
            self.conn.commit()

    def select(self, hash_str: str):
        self.cursor.execute('''
        SELECT * FROM Cache
        WHERE hash_str = ?
        ''', (hash_str,))
        return self.cursor.fetchone()

    def select_all(self):
        self.cursor.execute('''
        SELECT * FROM Cache
        ''')
        return self.cursor.fetchall()

    def select_all_expired(self):
        self.cursor.execute('''
        SELECT * FROM Cache
        WHERE expiry_time < CURRENT_TIMESTAMP
        ''')
        return self.cursor.fetchall()

    def select_all_newly_expired(self):
        self.cursor.execute('''
        SELECT * FROM Cache
        WHERE expiry_time < CURRENT_TIMESTAMP
        AND deleted_at IS NULL
        ''')
        return self.cursor.fetchall()

    def select_all_not_expired(self):
        self.cursor.execute('''
        SELECT * FROM Cache
        WHERE expiry_time >= CURRENT_TIMESTAMP AND deleted_at IS NULL
        ''')
        return self.cursor.fetchall()

    def delete_all_expired(self, auto_commit: bool = True):
        self.cursor.execute('''
        UPDATE Cache
        SET deleted_at = CURRENT_TIMESTAMP
        WHERE expiry_time < CURRENT_TIMESTAMP AND deleted_at IS NULL
        ''')
        if auto_commit:
            self.conn.commit()

    def delete_all(self, auto_commit: bool = True):
        self.cursor.execute('''
        UPDATE Cache
        SET deleted_at = CURRENT_TIMESTAMP
        ''')
        if auto_commit:
            self.conn.commit()
