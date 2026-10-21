import sqlite3
from app.config import DB_NAME


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabla de usuarios.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            picture TEXT,
            rol TEXT NOT NULL DEFAULT 'USUARIO'
        )
    """)

    # Tabla de solicitudes de trabajo.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS solicitudes_trabajo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            usuario_id INTEGER NOT NULL,

            display_name TEXT NOT NULL,
            roblox_username TEXT NOT NULL,
            email TEXT NOT NULL,
            discord_username TEXT NOT NULL,

            position TEXT NOT NULL,
            secondary_positions TEXT,
            experience_level TEXT NOT NULL,
            timezone TEXT NOT NULL,
            weekly_hours INTEGER NOT NULL,
            unavailable_times TEXT,
            tools TEXT,
            portfolio_url TEXT,
            relevant_experience TEXT,
            collaboration_type TEXT NOT NULL,

            motivation TEXT NOT NULL,
            current_learning TEXT NOT NULL,
            deadline_response TEXT NOT NULL,
            communication TEXT NOT NULL,
            feedback_response TEXT NOT NULL,
            teamwork_example TEXT NOT NULL,
            collaboration_conditions TEXT NOT NULL,
            authorship_details TEXT NOT NULL,

            authorship_confirmed INTEGER NOT NULL DEFAULT 0,
            privacy_consent INTEGER NOT NULL DEFAULT 0,

            estado TEXT NOT NULL DEFAULT 'pendiente',
            fecha_solicitud DATETIME NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (usuario_id)
                REFERENCES usuarios(id)
                ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()