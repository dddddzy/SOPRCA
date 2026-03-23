"""
base_store.py - 存储基类
"""

import sqlite3


class BaseStore:
    """存储基类"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)
