import sqlite3
from app.config import DB_NAME

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            picture TEXT,
            rol TEXT DEFAULT 'USER'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            completada BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()