
import hashlib

from fastapi import Cookie, Depends, HTTPException
from mysql.connector import Error

from db import conectar_db


def obtener_usuario_actual(
    dps_session: str | None = Cookie(default=None),
):
    if not dps_session:
        raise HTTPException(
            status_code=401,
            detail="Debes iniciar sesión",
        )

    token_hash = hashlib.sha256(
        dps_session.encode("utf-8")
    ).hexdigest()

    conexion = None
    cursor = None

    try:
        conexion = conectar_db()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                u.id,
                u.google_sub,
                u.correo,
                u.nombre,
                u.foto_url,
                u.rol
            FROM sesiones s
            JOIN usuarios u ON u.id = s.usuario_id
            WHERE s.token_hash = %s
              AND s.revocada_en IS NULL
              AND s.expira_en > UTC_TIMESTAMP()
            LIMIT 1
            """,
            (token_hash,),
        )

        usuario = cursor.fetchone()

        if usuario is None:
            raise HTTPException(
                status_code=401,
                detail="La sesión no existe o ha expirado",
            )

        return usuario

    except HTTPException:
        raise
    except Error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible verificar la sesión",
        )
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()


def requerir_admin(
    usuario: dict = Depends(obtener_usuario_actual),
):
    if usuario["rol"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para esta operación",
        )

    return usuario
