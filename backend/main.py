
import os
import time
from typing import Literal

import mysql.connector
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from mysql.connector import Error

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API de solicitudes de trabajo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bewareOfTheRat.nanadev.online",
        "http://localhost:4321",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Conexion a MySQL
def conectar_db():
    for intento in range(10):
        try:
            return mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "3306")),
                user=os.getenv("DB_USER", "api_user"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "registros_db"),
            )
        except Error:
            if intento == 9:
                raise HTTPException(
                    status_code=503,
                    detail="No fue posible conectar con MySQL",
                )
            time.sleep(2)


# Datos que se reciben al crear una solicitud
class SolicitudCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    correo: str = Field(min_length=1, max_length=150)
    telefono: str | None = Field(default=None, max_length=20)
    experiencia: str | None = None


# Estados permitidos para una solicitud
class CambiarEstado(BaseModel):
    estado: Literal["aceptada", "rechazada"]


@app.get("/")
def inicio():
    return {"mensaje": "API de solicitudes funcionando"}


# Crear una solicitud de trabajo
@app.post("/solicitudes", status_code=201)
def crear_solicitud(solicitud: SolicitudCrear):
    conexion = conectar_db()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO solicitudes_trabajo
                (nombre, correo, telefono, experiencia)
            VALUES (%s, %s, %s, %s)
            """,
            (
                solicitud.nombre,
                solicitud.correo,
                solicitud.telefono,
                solicitud.experiencia,
            ),
        )

        conexion.commit()
        nuevo_id = cursor.lastrowid

        return {
            "mensaje": "Solicitud creada correctamente",
            "id": nuevo_id,
            "estado": "pendiente",
        }

    except Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="No fue posible crear la solicitud",
        )
    finally:
        conexion.close()

# Consultar todas las solicitudes
@app.get("/solicitudes")
def listar_solicitudes(
    estado: Literal["pendiente", "aceptada", "rechazada"] | None = Query(
        default=None
    )
):
    conexion = None
    cursor = None

    try:
        # Conectar dentro del try para capturar errores de conexión
        conexion = conectar_db()
        cursor = conexion.cursor(dictionary=True)

        if estado:
            cursor.execute(
                """
                SELECT id, nombre, correo, telefono, experiencia,
                       estado, fecha_solicitud
                FROM solicitudes_trabajo
                WHERE estado = %s
                ORDER BY fecha_solicitud DESC
                """,
                (estado,),
            )
        else:
            cursor.execute(
                """
                SELECT id, nombre, correo, telefono, experiencia,
                       estado, fecha_solicitud
                FROM solicitudes_trabajo
                ORDER BY fecha_solicitud DESC
                """
            )

        return cursor.fetchall()

    except HTTPException:
        # Mantener los errores HTTP generados por conectar_db()
        raise

    except Exception as e:
        print(f"ERROR EN GET /solicitudes: {type(e).__name__}: {e}")

        raise HTTPException(
            status_code=500,
            detail={
                "mensaje": "No fue posible consultar las solicitudes",
                "tipo_error": type(e).__name__,
                "error": str(e),
            },
        )

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()

# Consultar una solicitud por su ID
@app.get("/solicitudes/{numero}")
def obtener_solicitud(numero: int):
    conexion = conectar_db()

    try:
        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, nombre, correo, telefono, experiencia,
                   estado, fecha_solicitud
            FROM solicitudes_trabajo
            WHERE id = %s
            """,
            (numero,),
        )

        solicitud = cursor.fetchone()

        if solicitud is None:
            raise HTTPException(
                status_code=404,
                detail="La solicitud no existe",
            )

        return solicitud

    except Error:
        raise HTTPException(
            status_code=500,
            detail="No fue posible consultar la solicitud",
        )
    finally:
        conexion.close()


# Aceptar o rechazar una solicitud
@app.patch("/solicitudes/{numero}/estado")
def cambiar_estado(numero: int, cambio: CambiarEstado):
    conexion = conectar_db()

    try:
        cursor = conexion.cursor()

        cursor.execute(
            """
            UPDATE solicitudes_trabajo
            SET estado = %s
            WHERE id = %s
            """,
            (cambio.estado, numero),
        )

        if cursor.rowcount == 0:
            cursor.execute(
                "SELECT id FROM solicitudes_trabajo WHERE id = %s",
                (numero,),
            )

            if cursor.fetchone() is None:
                raise HTTPException(
                    status_code=404,
                    detail="La solicitud no existe",
                )

        conexion.commit()

        return {
            "mensaje": "Estado actualizado correctamente",
            "id": numero,
            "estado": cambio.estado,
        }

    except Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="No fue posible actualizar el estado",
        )
    finally:
        conexion.close()
