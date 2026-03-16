from .base import QueryAdapter
import sqlite3


class SQLiteAdapter(QueryAdapter):
    def __init__(self, db_path):
        self.db_path = db_path

    def execute_scalar(self, sql):
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def execute_rows(self, sql):
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()
        finally:
            conn.close()
