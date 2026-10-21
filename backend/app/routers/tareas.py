
import sqlite3

from fastapi import APIRouter, HTTPException, status

from app.database import get_db_connection
from app.models.models import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/tareas", tags=["Tareas"])


# ==========================================
# CREATE: crear una tarea
# POST /tareas/
# ==========================================

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def crear_tarea(datos: TaskCreate):
    conn = get_db_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO tareas (title, description)
            VALUES (?, ?)
            """,
            (datos.title, datos.description),
        )

        conn.commit()

        tarea = conn.execute(
            "SELECT * FROM tareas WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

        return dict(tarea)

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una tarea con ese título.",
        )

    finally:
        conn.close()


# ==========================================
# READ: listar todas las tareas
# GET /tareas/
# ==========================================

@router.get("/", response_model=list[TaskResponse])
def listar_tareas():
    conn = get_db_connection()

    try:
        tareas = conn.execute(
            "SELECT * FROM tareas ORDER BY id DESC"
        ).fetchall()

        return [dict(tarea) for tarea in tareas]

    finally:
        conn.close()


# ==========================================
# READ: consultar una tarea por ID
# GET /tareas/1
# ==========================================

@router.get("/{tarea_id}", response_model=TaskResponse)
def obtener_tarea(tarea_id: int):
    conn = get_db_connection()

    try:
        tarea = conn.execute(
            "SELECT * FROM tareas WHERE id = ?",
            (tarea_id,),
        ).fetchone()

        if not tarea:
            raise HTTPException(
                status_code=404,
                detail="Tarea no encontrada.",
            )

        return dict(tarea)

    finally:
        conn.close()


# ==========================================
# UPDATE: actualizar una tarea
# PUT /tareas/1
# ==========================================

@router.put("/{tarea_id}", response_model=TaskResponse)
def actualizar_tarea(tarea_id: int, datos: TaskUpdate):
    conn = get_db_connection()

    try:
        tarea = conn.execute(
            "SELECT * FROM tareas WHERE id = ?",
            (tarea_id,),
        ).fetchone()

        if not tarea:
            raise HTTPException(
                status_code=404,
                detail="Tarea no encontrada.",
            )

        cambios = datos.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        if cambios:
            campos = ", ".join(
                f"{campo} = ?" for campo in cambios
            )
            valores = list(cambios.values()) + [tarea_id]

            conn.execute(
                f"UPDATE tareas SET {campos} WHERE id = ?",
                valores,
            )
            conn.commit()

        tarea_actualizada = conn.execute(
            "SELECT * FROM tareas WHERE id = ?",
            (tarea_id,),
        ).fetchone()

        return dict(tarea_actualizada)

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una tarea con ese título.",
        )

    finally:
        conn.close()


# ==========================================
# DELETE: eliminar una tarea
# DELETE /tareas/1
# ==========================================

@router.delete("/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    conn = get_db_connection()

    try:
        tarea = conn.execute(
            "SELECT id FROM tareas WHERE id = ?",
            (tarea_id,),
        ).fetchone()

        if not tarea:
            raise HTTPException(
                status_code=404,
                detail="Tarea no encontrada.",
            )

        conn.execute(
            "DELETE FROM tareas WHERE id = ?",
            (tarea_id,),
        )

        conn.commit()

        return {
            "mensaje": "Tarea eliminada correctamente.",
            "id": tarea_id,
        }

    finally:
        conn.close()
