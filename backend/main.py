import sqlite3
from typing import List, Optional
from enum import Enum
from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests

GOOGLE_CLIENT_ID = "711422571578-b9s5pq7oi0gtgmml3s1dk44fbhfj9663.apps.googleusercontent.com"

app = FastAPI(
    title="API Dream Projects Studio - Modo Pruebas",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RoleEnum(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    EDITOR = "EDITOR"

def init_db():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            picture TEXT,
            rol TEXT DEFAULT 'USER'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            completada BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

class GoogleLoginRequest(BaseModel):
    token: str

class UserResponse(BaseModel):
    id: int
    email: str
    nombre: str
    picture: Optional[str] = None
    rol: RoleEnum

class RoleUpdateRequest(BaseModel):
    email: str
    nuevo_rol: RoleEnum

class TareaCrear(BaseModel):
    titulo: str

class Tarea(BaseModel):
    id: int
    titulo: str
    completada: bool

def get_user_by_email(email: str):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, nombre, picture, rol FROM usuarios WHERE email = ?", (email,))
    fila = cursor.fetchone()
    conn.close()
    if fila:
        return {"id": fila[0], "email": fila[1], "nombre": fila[2], "picture": fila[3], "rol": fila[4]}
    return None

def upsert_google_user(email: str, nombre: str, picture: str):
    user = get_user_by_email(email)
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    if not user:
        cursor.execute(
            "INSERT INTO usuarios (email, nombre, picture, rol) VALUES (?, ?, ?, ?)",
            (email, nombre, picture, RoleEnum.USER.value)
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

# Dependencia flexible que NO bloquea, pero captura errores y detalla por qué falla
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
        # Devuelve el error exacto en los logs o respuesta para depurar
        print(f"Error validando token: {str(e)}")
        return None

# Endpoints de Autenticación
@app.post("/auth/google", response_model=UserResponse)
def login_google(payload: GoogleLoginRequest):
    try:
        id_info = id_token.verify_oauth2_token(payload.token, requests.Request(), GOOGLE_CLIENT_ID)
        email = id_info.get("email")
        nombre = id_info.get("name", "Usuario")
        picture = id_info.get("picture", "")

        user = upsert_google_user(email, nombre, picture)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error detallado de Google Auth: {str(e)}")

@app.get("/auth/me", response_model=UserResponse)
def get_my_profile(authorization: Optional[str] = Header(None)):
    user = get_current_user_optional(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="No se pudo autenticar al usuario. Token ausente o inválido.")
    return user

# Gestión de Usuarios (Abierta para pruebas)
@app.get("/admin/usuarios", response_model=List[UserResponse])
def listar_usuarios():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, nombre, picture, rol FROM usuarios ORDER BY id DESC")
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "email": f[1], "nombre": f[2], "picture": f[3], "rol": f[4]} for f in filas]

@app.put("/admin/cambiar-rol", response_model=UserResponse)
def cambiar_rol_usuario(payload: RoleUpdateRequest):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET rol = ? WHERE email = ?", (payload.nuevo_rol.value, payload.email))
    conn.commit()
    conn.close()

    updated_user = get_user_by_email(payload.email)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en la base de datos")
    return updated_user

@app.delete("/admin/usuarios/{email}")
def eliminar_usuario(email: str):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return {"mensaje": f"Usuario {email} eliminado con éxito"}

# Rutas de prueba (abiertas para comprobar si el usuario tiene un rol u otro sin bloquearte)
@app.get("/rutas/publica")
def ruta_publica(authorization: Optional[str] = Header(None)):
    user = get_current_user_optional(authorization)
    return {
        "acceso": "permitido",
        "mensaje": "¡Estás en la ruta pública!",
        "usuario_logueado": user["nombre"] if user else "Anónimo / No logueado",
        "tu_rol": user["rol"] if user else "N/A"
    }

@app.get("/rutas/editor")
def ruta_editor(authorization: Optional[str] = Header(None)):
    user = get_current_user_optional(authorization)
    rol = user["rol"] if user else "ANONIMO"
    # Aquí puedes simular la comprobación de permisos para ver si pasaría o no
    tiene_permiso = rol in ["EDITOR", "ADMIN"]
    return {
        "acceso": "simulado",
        "mensaje": "Ruta de Editor evaluada",
        "tu_rol_actual": rol,
        "tiene_permiso_requerido": tiene_permiso
    }

@app.get("/rutas/admin")
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

# Tareas CRUD
@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, completada FROM tareas")
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "titulo": f[1], "completada": bool(f[2])} for f in filas]

@app.post("/tareas", response_model=Tarea)
def crear_tarea(tarea: TareaCrear):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tareas (titulo, completada) VALUES (?, ?)", (tarea.titulo, False))
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    return {"id": tarea_id, "titulo": tarea.titulo, "completada": False}