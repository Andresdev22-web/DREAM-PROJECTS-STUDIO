from datetime import datetime, timedelta, timezone

import jwt
from google.auth.transport import requests
from google.oauth2 import id_token

from app.config import (
    GOOGLE_CLIENT_ID,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.database import get_db_connection
from app.models.models import RoleEnum


def get_user_by_email(email: str):
    conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, email, nombre, picture, rol
            FROM usuarios
            WHERE email = ?
            """,
            (email,),
        )
        fila = cursor.fetchone()
        return dict(fila) if fila else None
    finally:
        conn.close()


def get_user_by_id(user_id: int):
    conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, email, nombre, picture, rol
            FROM usuarios
            WHERE id = ?
            """,
            (user_id,),
        )
        fila = cursor.fetchone()
        return dict(fila) if fila else None
    finally:
        conn.close()


def upsert_google_user(email: str, nombre: str, picture: str):
    conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO usuarios (email, nombre, picture, rol)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                nombre = excluded.nombre,
                picture = excluded.picture
            """,
            (email, nombre, picture, RoleEnum.USUARIO.value),
        )
        conn.commit()
    finally:
        conn.close()

    return get_user_by_email(email)


def verify_google_token(token: str) -> dict:
    info = id_token.verify_oauth2_token(
        token,
        requests.Request(),
        GOOGLE_CLIENT_ID,
    )

    if not info.get("email") or info.get("email_verified") is not True:
        raise ValueError("Google no proporcionó un correo verificado.")

    return info


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def authenticate_google_user(google_token: str) -> dict:
    info = verify_google_token(google_token)

    user = upsert_google_user(
        email=info["email"],
        nombre=info.get("name") or "Usuario",
        picture=info.get("picture") or "",
    )

    access_token = create_access_token(user["id"])

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }