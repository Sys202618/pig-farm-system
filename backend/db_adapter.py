# -*- coding: utf-8 -*-
"""Database adapter: SQLite (local) / PostgreSQL (cloud)"""
import os
import sqlite3

DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    # Render's DATABASE_URL starts with postgres://, SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

class DatabaseConnection:
    """Wrapper that provides SQLite-like interface over PostgreSQL or SQLite"""
    
    def __init__(self, conn):
        self._conn = conn
        self._is_pg = USE_POSTGRES
    
    def cursor(self):
        return CursorWrapper(self._conn.cursor(), self._is_pg)
    
    def commit(self):
        self._conn.commit()
    
    def close(self):
        self._conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()

class CursorWrapper:
    """Cursor that translates SQLite SQL to PostgreSQL"""
    
    PG_TRANSLATIONS = [
        ("datetime('now')", 'NOW()'),
        ('datetime("now")', 'NOW()'),
        ("datetime('now',", 'NOW() + INTERVAL '),
        ('datetime("now",', 'NOW() + INTERVAL '),
        ('?', '%s'),
        ('AUTOINCREMENT', 'SERIAL'),
        ('INTEGER PRIMARY KEY', 'SERIAL PRIMARY KEY'),
    ]
    
    def __init__(self, cursor, is_pg):
        self._cursor = cursor
        self._is_pg = is_pg
    
    def _translate_sql(self, sql):
        if not self._is_pg:
            return sql
        
        # Handle SQLite date modifiers like datetime('now', '+7 days')
        import re
        
        # Replace ? with %s
        sql = sql.replace('?', '%s')
        
        # Handle datetime('now', '+7 days') -> NOW() + INTERVAL '7 days'
        def replace_datetime(match):
            inner = match.group(1)
            if inner == "'now'" or inner == '"now"':
                return 'NOW()'
            # Handle datetime('now', '+7 days')
            parts = inner.split(',')
            if len(parts) == 2 and ('now' in parts[0]):
                interval = parts[1].strip().strip("'\"")
                return f"NOW() + INTERVAL '{interval}'"
            return match.group(0)
        
        sql = re.sub(r"datetime\(([^)]+)\)", replace_datetime, sql)
        
        return sql
    
    def execute(self, sql, params=()):
        sql = self._translate_sql(sql)
        self._cursor.execute(sql, params)
        return self
    
    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        if self._is_pg:
            return dict(row) if hasattr(row, 'keys') else row
        return row  # SQLite Row is already dict-like via row_factory
    
    def fetchall(self):
        rows = self._cursor.fetchall()
        if self._is_pg:
            return [dict(r) if hasattr(r, 'keys') else r for r in rows]
        return rows
    
    def lastrowid(self):
        if self._is_pg:
            # PostgreSQL uses RETURNING id or currval
            self.execute("SELECT lastval()")
            return self.fetchone()['lastval']
        return self._cursor.lastrowid

def get_db_conn():
    """Get database connection (SQLite or PostgreSQL)"""
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        import os, sys
        if getattr(sys, 'frozen', False):
            BASE_DIR = os.path.dirname(sys.executable)
        else:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        DB_PATH = os.path.join(BASE_DIR, 'data', 'pig_farm.db')
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
    return DatabaseConnection(conn)

def init_postgres_tables(conn):
    """Initialize PostgreSQL tables (SQLite schema needs adjustments)"""
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(64) NOT NULL,
            role VARCHAR(20) DEFAULT 'user',
            token VARCHAR(64),
            token_exp TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    # Add default admin if not exists
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        import hashlib
        pw_hash = hashlib.md5('admin123'.encode()).hexdigest()
        c.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            ('admin', pw_hash, 'admin')
        )
    
    conn.commit()

# Export for app.py
__all__ = ['get_db_conn', 'USE_POSTGRES', 'init_postgres_tables']
