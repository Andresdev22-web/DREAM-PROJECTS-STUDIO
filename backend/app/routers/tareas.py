from typing import List, Optional
from fastapi import APIRouter, Header
from app.database import get_db_connection
from app.auth import get_current_user_optional
from app.models import Tarea, TareaCrear

router = APIRouter(tags=["Rutas y Tareas"])

@router.get("/rutas/publica")
def ruta_publica(authorization: Optional[str] = Header(None)):
    user = get_current_user_optional(authorization)
    return {
        "acceso": "permitido",
        "mensaje": "¡Estás en la ruta pública!",
        "usuario_logueado": user["nombre"] if user else "Anónimo / No logueado",
        "tu_rol": user["rol"] if user else "N/A"
    }

@router.get("/rutas/editor")
def ruta_editor(authorization: Optional[str] = Header(None)):
    user = get_current_user_optional(authorization)
    rol = user["rol"] if user else "ANONIMO"
    tiene_permiso = rol in ["EDITOR", "ADMIN"]
    return {
        "acceso": "simulado",
        "mensaje": "Ruta de Editor evaluada",
        "tu_rol_actual": rol,
        "tiene_permiso_requerido": tiene_permiso
    }

@router.get("/rutas/admin")
def ruta_admin(authorization: Optional[str] = Header(None)):
    user = get_current_user_optional(authorization)
    rol = user["rol"] if user else "ANONIMO"
    tiene_permiso = rol == "ADMIN"
    return {
        "acceso": "simulado",
        "mensaje": "Ruta de Administrador evaluada",
        "tu_rol_actual": rol,
        "tiene_permiso_requerido": tiene_permiso
    }

@router.get("/tareas", response_model=List[Tarea])
def obtener_tareas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, completada FROM tareas")
    filas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return filas

@router.post("/tareas", response_model=Tarea)
def crear_tarea(tarea: TareaCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tareas (titulo, completada) VALUES (?, ?)", (tarea.titulo, False))
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    return {"id": tarea_id, "titulo": tarea.titulo, "completada": False}