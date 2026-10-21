import sqlite3

from fastapi import APIRouter, HTTPException
from app.database import get_db_connection
from app.models.models import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


# ==========================================
# READ: listar todos los usuarios
# GET /usuarios/
# ==========================================

@router.get("/", response_model=list[UserResponse])
def listar_usuarios():
    conn = get_db_connection()

    try:
        usuarios = conn.execute(
            "SELECT * FROM usuarios ORDER BY id DESC"
        ).fetchall()

        return [dict(usuario) for usuario in usuarios]
    finally:
        conn.close()


# ==========================================
# READ: consultar un usuario
# GET /usuarios/1
# ==========================================

@router.get("/{usuario_id}", response_model=UserResponse)
def obtener_usuario(usuario_id: int):
    conn = get_db_connection()

    try:
        usuario = conn.execute(
            "SELECT * FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()

        if usuario is None:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado",
            )

        return dict(usuario)
    finally:
        conn.close()


# ==========================================
# CREATE: crear un usuario
# POST /usuarios/
# ==========================================

@router.post("/", response_model=UserResponse, status_code=201)
def crear_usuario(datos: UserCreate):
    conn = get_db_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO usuarios (email, nombre, picture, rol)
            VALUES (?, ?, ?, 'USUARIO')
            """,
            (datos.email, datos.nombre, datos.picture),
        )

        conn.commit()

        usuario = conn.execute(
            "SELECT * FROM usuarios WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

        return dict(usuario)

    except sqlite3.IntegrityError:
        conn.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un usuario con ese correo",
        )
    finally:
        conn.close()


# ==========================================
# UPDATE: actualizar un usuario
# PUT /usuarios/1
# ==========================================

@router.put("/{usuario_id}", response_model=UserResponse)
def actualizar_usuario(usuario_id: int, datos: UserUpdate):
    cambios = datos.model_dump(exclude_unset=True)

    if not cambios:
        raise HTTPException(
            status_code=400,
            detail="Debes enviar al menos un campo para actualizar",
        )

    conn = get_db_connection()

    try:
        usuario = conn.execute(
            "SELECT * FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()

        if usuario is None:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado",
            )

        # Solo permitimos modificar estos campos.
        campos_permitidos = {"email", "nombre", "picture", "rol"}
        cambios = {
            campo: valor
            for campo, valor in cambios.items()
            if campo in campos_permitidos
        }

        if not cambios:
            raise HTTPException(
                status_code=400,
                detail="No hay campos válidos para actualizar",
            )

        columnas = ", ".join(
            f"{campo} = ?" for campo in cambios
        )

        valores = list(cambios.values())
        valores.append(usuario_id)

        conn.execute(
            f"UPDATE usuarios SET {columnas} WHERE id = ?",
            valores,
        )

        conn.commit()

        actualizado = conn.execute(
            "SELECT * FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()

        return dict(actualizado)

    except sqlite3.IntegrityError:
        conn.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ese correo ya pertenece a otro usuario",
        )
    finally:
        conn.close()


# ==========================================
# DELETE: eliminar un usuario
# DELETE /usuarios/1
# ==========================================

@router.delete("/{usuario_id}")
def eliminar_usuario(usuario_id: int):
    conn = get_db_connection()

    try:
        cursor = conn.execute(
            "DELETE FROM usuarios WHERE id = ?",
            (usuario_id,),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado",
            )

        conn.commit()

        return {
            "mensaje": "Usuario eliminado correctamente",
            "id": usuario_id,
        }
    finally:
        conn.close()