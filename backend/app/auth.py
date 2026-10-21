from typing import Optional
from fastapi import Header
from google.oauth2 import id_token
from google.auth.transport import requests
from app.config import GOOGLE_CLIENT_ID
from app.database import get_db_connection
from app.models import RoleEnum

def get_user_by_email(email: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, nombre, picture, rol FROM usuarios WHERE email = ?", (email,))
    fila = cursor.fetchone()
    conn.close()
    if fila:
        return dict(fila)
    return None

def upsert_google_user(email: str, nombre: str, picture: str):
    user = get_user_by_email(email)
    conn = get_db_connection()
    cursor = conn.cursor()
    if not user:
        cursor.execute(
            "INSERT INTO usuarios (email, nombre, picture, rol) VALUES (?, ?, ?, ?)",
            (email, nombre, picture, RoleEnum.USUARIO.value)
        )
        conn.commit()
    else:
        cursor.execute(
            "UPDATE usuarios SET nombre = ?, picture = ? WHERE email = ?",
            (nombre, picture, email)
        )
        conn.commit()
    conn.close()
    return get_user_by_email(email)

def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    try:
        id_info = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        email = id_info.get("email")
        user = get_user_by_email(email)
        if not user:
            user = upsert_google_user(email, id_info.get("name", "Usuario"), id_info.get("picture", ""))
        return user
    except Exception as e:
        print(f"Error validando token: {str(e)}")
        return None