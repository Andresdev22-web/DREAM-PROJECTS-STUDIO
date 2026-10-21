
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================================================
# ROLES
# ==================================================

class RoleEnum(str, Enum):
    USUARIO = "USUARIO"
    CLIENTE = "CLIENTE"
    SOLICITANTE = "SOLICITANTE"
    TRABAJADOR = "TRABAJADOR"
    ADMINISTRADOR = "ADMINISTRADOR"


# ==================================================
# AUTENTICACIÓN Y USUARIOS
# ==================================================


class GoogleLoginRequest(BaseModel):
    token: str


class UserResponse(BaseModel):
    id: int
    email: str
    nombre: str
    picture: str | None = None
    rol: RoleEnum


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse




# ==================================================
# AUTENTICACIÓN Y USUARIOS
# ==================================================


class UserCreate(BaseModel):
    email: str
    nombre: str
    picture: Optional[str] = None
    rol: Optional[RoleEnum] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    nombre: Optional[str] = None
    picture: Optional[str] = None
    rol: Optional[RoleEnum] = None







# ==================================================
# TAREAS
# ==================================================



class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str