from enum import Enum
from typing import Optional
from pydantic import BaseModel

class RoleEnum(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    EDITOR = "EDITOR"

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