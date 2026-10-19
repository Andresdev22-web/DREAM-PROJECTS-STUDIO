import sqlite3
from typing import List, Optional
from enum import Enum
from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests

# Configuración de Google Client ID
GOOGLE_CLIENT_ID = "711422571578-b9s5pq7oi0gtgmml3s1dk44fbhfj9663.apps.googleusercontent.com"

app = FastAPI(
    title="API Dream Projects Studio - Google Auth & Roles",
    version="2.0.0"
)

# ------------------------------------------------------------------------------
# 1. CORS
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# 2. Roles Enum & Base de Datos
# ------------------------------------------------------------------------------
class RoleEnum(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    EDITOR = "EDITOR"

def init_db():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    # Tabla de Usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            picture TEXT,
            rol TEXT DEFAULT 'USER'
        )
    """)
    # Tabla de Tareas
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

# ------------------------------------------------------------------------------
# 3. Modelos Pydantic
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# 4. Funciones Auxiliares de Base de Datos
# ------------------------------------------------------------------------------
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
        # Si es el primer usuario en registrarse o correo específico, asigna rol por defecto 'USER'
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

# ------------------------------------------------------------------------------
# 5. Sistema de Autenticación & Control de Acceso por Roles (RBAC Dependencies)
# ------------------------------------------------------------------------------
def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorización no provisto o con formato inválido ('Bearer <token>')"
        )
    
    token = authorization.split(" ")[1]
    
    try:
        # Verificar el token directamente contra los servidores públicos de Google
        id_info = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        email = id_info.get("email")
        
        user = get_user_by_email(email)
        if not user:
            # En caso de que se haya validado el token pero no exista en la DB
            user = upsert_google_user(
                email=email,
                nombre=id_info.get("name", "Usuario"),
                picture=id_info.get("picture", "")
            )
        return user

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de Google inválido o expirado"
        )

def require_roles(allowed_roles: List[RoleEnum]):
    """
    Dependencia genérica para restringir rutas a roles específicos.
    Ejemplo de uso: Depends(require_roles([RoleEnum.ADMIN, RoleEnum.EDITOR]))
    """
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["rol"] not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: Se requiere alguno de los siguientes roles: {[r.value for r in allowed_roles]}. Tu rol actual es: {current_user['rol']}"
            )
        return current_user
    return role_checker

# ------------------------------------------------------------------------------
# 6. Endpoints de Autenticación y Administración
# ------------------------------------------------------------------------------

@app.post("/auth/google", response_model=UserResponse)
def login_google(payload: GoogleLoginRequest):
    """
    Recibe el JWT ID Token de Google enviado desde el frontend, lo valida,
    registra o actualiza al usuario y devuelve sus datos con su Rol asignado.
    """
    try:
        id_info = id_token.verify_oauth2_token(payload.token, requests.Request(), GOOGLE_CLIENT_ID)
        email = id_info.get("email")
        nombre = id_info.get("name", "Usuario")
        picture = id_info.get("picture", "")

        user = upsert_google_user(email, nombre, picture)
        return user
    except ValueError:
        raise HTTPException(status_code=400, detail="Token de Google inválido")

@app.get("/auth/me", response_model=UserResponse)
def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Obtiene el perfil completo del usuario autenticado."""
    return current_user

@app.get("/admin/usuarios", response_model=List[UserResponse])
def listar_usuarios(current_user: dict = Depends(require_roles([RoleEnum.ADMIN]))):
    """[SOLO ADMIN] Lista todos los usuarios registrados."""
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, nombre, picture, rol FROM usuarios")
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "email": f[1], "nombre": f[2], "picture": f[3], "rol": f[4]} for f in filas]

@app.put("/admin/cambiar-rol", response_model=UserResponse)
def cambiar_rol_usuario(
    payload: RoleUpdateRequest,
    current_user: dict = Depends(get_current_user) # Permitimos que cualquiera ejecute para facilitar pruebas
):
    """
    Permite cambiar el rol de cualquier usuario por email para realizar pruebas.
    """
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET rol = ? WHERE email = ?", (payload.nuevo_rol.value, payload.email))
    conn.commit()
    conn.close()

    updated_user = get_user_by_email(payload.email)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return updated_user

# ------------------------------------------------------------------------------
# 7. Rutas Demostrativas Protegidas por Roles
# ------------------------------------------------------------------------------

# Ruta publica / para cualquier usuario autenticado (USER, EDITOR, ADMIN)
@app.get("/rutas/publica")
def ruta_publica(current_user: dict = Depends(require_roles([RoleEnum.USER, RoleEnum.EDITOR, RoleEnum.ADMIN]))):
    return {
        "mensaje": "¡Bienvenido a la ruta pública!",
        "usuario": current_user["nombre"],
        "tu_rol": current_user["rol"]
    }

# Ruta restringida a EDITOR o ADMIN
@app.get("/rutas/editor")
def ruta_editor(current_user: dict = Depends(require_roles([RoleEnum.EDITOR, RoleEnum.ADMIN]))):
    return {
        "mensaje": "¡Acceso concedido a la Zona de Editores!",
        "usuario": current_user["nombre"],
        "tu_rol": current_user["rol"]
    }

# Ruta restringida EXCLUSIVAMENTE a ADMIN
@app.get("/rutas/admin")
def ruta_admin(current_user: dict = Depends(require_roles([RoleEnum.ADMIN]))):
    return {
        "mensaje": "¡Acceso concedido a la Zona de Administración Privada!",
        "usuario": current_user["nombre"],
        "tu_rol": current_user["rol"]
    }

# CRUD de Tareas
@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, completada FROM tareas")
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "titulo": f[1], "completada": bool(f[2])} for f in filas]

@app.post("/tareas", response_model=Tarea)
def crear_tarea(
    tarea: TareaCrear, 
    current_user: dict = Depends(require_roles([RoleEnum.EDITOR, RoleEnum.ADMIN]))
):
    """Crear tareas requiere rol EDITOR o ADMIN."""
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tareas (titulo, completada) VALUES (?, ?)", (tarea.titulo, False))
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    return {"id": tarea_id, "titulo": tarea.titulo, "completada": False}




@app.get("/admin/usuarios", response_model=List[UserResponse])
def listar_usuarios(current_user: dict = Depends(get_current_user)):
    """Lista todos los usuarios registrados en la base de datos."""
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, nombre, picture, rol FROM usuarios ORDER BY id DESC")
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "email": f[1], "nombre": f[2], "picture": f[3], "rol": f[4]} for f in filas]

@app.delete("/admin/usuarios/{email}")
def eliminar_usuario(email: str, current_user: dict = Depends(get_current_user)):
    """Elimina un usuario de la base de datos por email."""
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return {"mensaje": f"Usuario {email} eliminado con éxito"}