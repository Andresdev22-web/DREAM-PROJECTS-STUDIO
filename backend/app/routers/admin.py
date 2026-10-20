from typing import List
from fastapi import APIRouter, HTTPException
from app.database import get_db_connection
from app.models import UserResponse, RoleUpdateRequest

router = APIRouter(prefix="/admin", tags=["Administración"])

@router.get("/usuarios", response_model=List[UserResponse])
def listar_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, nombre, picture, rol FROM usuarios ORDER BY id DESC")
    filas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return filas

@router.put("/cambiar-rol", response_model=UserResponse)
def cambiar_rol_usuario(payload: RoleUpdateRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET rol = ? WHERE email = ?", (payload.nuevo_rol.value, payload.email))
    conn.commit()
    conn.close()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, nombre, picture, rol FROM usuarios WHERE email = ?", (payload.email,))
    updated_user = cursor.fetchone()
    conn.close()

    if not updated_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en la base de datos")
    return dict(updated_user)

@router.delete("/usuarios/{email}")
def eliminar_usuario(email: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return {"mensaje": f"Usuario {email} eliminado con éxito"}