
import os
import time

import mysql.connector
from fastapi import FastAPI, HTTPException
from mysql.connector import Error

app = FastAPI(title="API de registros")


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


@app.get("/")
def inicio():
    return {"mensaje": "API funcionando"}


@app.get("/crear/{dato}")
def crear(dato: str):
    conexion = conectar_db()

    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO registros (dato) VALUES (%s)",
            (dato,),
        )
        conexion.commit()

        return {
            "mensaje": "Registro creado",
            "id": cursor.lastrowid,
            "dato": dato,
        }
    except Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="No fue posible crear el registro",
        )
    finally:
        conexion.close()


@app.get("/lista")
def lista():
    conexion = conectar_db()

    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, dato FROM registros ORDER BY id DESC"
        )
        return cursor.fetchall()
    except Error:
        raise HTTPException(
            status_code=500,
            detail="No fue posible consultar los registros",
        )
    finally:
        conexion.close()


@app.get("/eliminar/{numero}")
def eliminar(numero: int):
    conexion = conectar_db()

    try:
        cursor = conexion.cursor()
        cursor.execute(
            "DELETE FROM registros WHERE id = %s",
            (numero,),
        )
        conexion.commit()

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="El registro no existe",
            )

        return {
            "mensaje": "Registro eliminado",
            "id": numero,
        }
    except Error:
        conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail="No fue posible eliminar el registro",
        )
    finally:
        conexion.close()
