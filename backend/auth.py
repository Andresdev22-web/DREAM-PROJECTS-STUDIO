
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from mysql.connector import Error

from db import conectar_db
from dependencies import obtener_usuario_actual
from oauth import oauth

router = APIRouter(prefix="/auth", tags=["Autenticación"])

FRONTEND_URL = os.environ["FRONTEND_URL"]
GOOGLE_REDIRECT_URI = os.environ["GOOGLE_REDIRECT_URI"]

COOKIE_SECURE = (
    os.environ.get("COOKIE_SECURE", "true").lower() == "true"
)
SESSION_DURATION = 7 * 24 * 60 * 60


@router.get("/google/login")
async def login_google(request: Request):
    return await oauth.google.authorize_redirect(
        request,
        GOOGLE_REDIRECT_URI,
    )


@router.get("/google/callback")
async def callback_google(request: Request):
    # Authlib valida el estado OAuth y procesa la respuesta de Google.
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="No se pudo completar el inicio de sesión con Google",
        )

    info = token.get("userinfo")

    if not info:
        raise HTTPException(
            status_code=401,
            detail="Google no proporcionó información verificable",
        )

    if not info.get("sub") or not info.get("email"):
        raise HTTPException(
            status_code=401,
            detail="Faltan datos de identidad de Google",
        )

    if info.get("email_verified") is not True:
        raise HTTPException(
            status_code=403,
            detail="El correo de Google no está verificado",
        )

    google_sub = info["sub"]
    correo = info["email"]
    nombre = info.get("name") or correo
    foto_url = info.get("picture")

    conexion = None
    cursor = None
    raw_session = None

    try:
        conexion = conectar_db()
        cursor = conexion.cursor(dictionary=True)

        # Crear el usuario la primera vez.
        # Si ya existe por google_sub, actualizar sus datos.
        cursor.execute(
            """
            INSERT INTO usuarios
                (google_sub, correo, nombre, foto_url)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                correo = VALUES(correo),
                nombre = VALUES(nombre),
                foto_url = VALUES(foto_url)
            """,
            (google_sub, correo, nombre, foto_url),
        )

        cursor.execute(
            """
            SELECT id, rol
            FROM usuarios
            WHERE google_sub = %s
            """,
            (google_sub,),
        )
        usuario = cursor.fetchone()

        if usuario is None:
            raise HTTPException(
                status_code=500,
                detail="No fue posible registrar al usuario",
            )

        # Crear un secreto nuevo para la sesión.
        raw_session = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(
            raw_session.encode("utf-8")
        ).hexdigest()

        expira_en = (
            datetime.now(timezone.utc).replace(tzinfo=None)
            + timedelta(seconds=SESSION_DURATION)
        )

        cursor.execute(
            """
            INSERT INTO sesiones
                (usuario_id, token_hash, expira_en)
            VALUES (%s, %s, %s)
            """,
            (usuario["id"], token_hash, expira_en),
        )

        conexion.commit()

    except HTTPException:
        if conexion is not None:
            conexion.rollback()
        raise

    except Error:
        if conexion is not None:
            conexion.rollback()
        raise HTTPException(
            status_code=503,
            detail="No fue posible crear la sesión",
        )

    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

    # Volver al frontend y entregar la cookie de sesión.
    respuesta = RedirectResponse(
        url=FRONTEND_URL,
        status_code=303,
    )

    respuesta.set_cookie(
        key="dps_session",
        value=raw_session,
        max_age=SESSION_DURATION,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )

    return respuesta


@router.get("/me")
def mi_sesion(
    usuario: dict = Depends(obtener_usuario_actual),
):
    return {
        "autenticado": True,
        "usuario": {
            "id": usuario["id"],
            "correo": usuario["correo"],
            "nombre": usuario["nombre"],
            "foto_url": usuario["foto_url"],
            "rol": usuario["rol"],
        },
    }


@router.post("/logout")
def cerrar_sesion(
    usuario: dict = Depends(obtener_usuario_actual),
    request: Request = None,
):
    # La cookie se lee para revocar exclusivamente esa sesión.
    raw_session = request.cookies.get("dps_session") if request else None

    if not raw_session:
        raise HTTPException(
            status_code=401,
            detail="No hay una sesión válida",
        )

    token_hash = hashlib.sha256(
        raw_session.encode("utf-8")
    ).hexdigest()

    conexion = None
    cursor = None

    try:
        conexion = conectar_db()
        cursor = conexion.cursor()

        cursor.execute(
            """
            UPDATE sesiones
            SET revocada_en = UTC_TIMESTAMP()
            WHERE token_hash = %s
              AND usuario_id = %s
              AND revocada_en IS NULL
            """,
            (token_hash, usuario["id"]),
        )

        conexion.commit()

    except Error:
        if conexion is not None:
            conexion.rollback()
        raise HTTPException(
            status_code=503,
            detail="No fue posible cerrar la sesión",
        )

    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

    respuesta = RedirectResponse(
        url=FRONTEND_URL,
        status_code=303,
    )
    respuesta.delete_cookie(
        key="dps_session",
        path="/",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )

    return respuesta
