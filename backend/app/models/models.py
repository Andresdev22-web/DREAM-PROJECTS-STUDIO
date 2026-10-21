
from datetime import datetime
from enum import Enum
from typing import Optional ,Literal

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



# ==================================================
# SOLICITUDES DE TRABAJO
# ==================================================



class CandidateCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    display_name: str = Field(min_length=1, max_length=100)
    roblox_username: str = Field(min_length=1, max_length=100)
    email: str
    discord_username: str | None = None


class ProfileCreate(BaseModel):
    position: str = Field(min_length=1, max_length=100)
    secondary_positions: str | None = None
    experience_level: str = Field(min_length=1, max_length=50)
    timezone: str = Field(min_length=1, max_length=100)
    weekly_hours: int = Field(ge=1, le=168)
    unavailable_times: str | None = None
    tools: str | None = None
    portfolio_url: str | None = None
    relevant_experience: str | None = None
    collaboration_type: str = Field(min_length=1, max_length=50)


class AnswersCreate(BaseModel):
    motivation: str = Field(min_length=1)
    current_learning: str = Field(min_length=1)
    deadline_response: str = Field(min_length=1)
    communication: str = Field(min_length=1)
    feedback_response: str = Field(min_length=1)
    teamwork_example: str = Field(min_length=1)
    collaboration_conditions: str = Field(min_length=1)
    authorship_details: str = Field(min_length=1)


class DeclarationsCreate(BaseModel):
    authorship_confirmed: bool
    privacy_consent: bool


class SolicitudCreate(BaseModel):
    candidate: CandidateCreate
    profile: ProfileCreate
    answers: AnswersCreate
    declarations: DeclarationsCreate


class SolicitudResponse(BaseModel):
    id: int
    usuario_id: int
    display_name: str
    roblox_username: str
    email: str
    discord_username: str | None
    position: str
    secondary_positions: str | None
    experience_level: str
    timezone: str
    weekly_hours: int
    unavailable_times: str | None
    tools: str | None
    portfolio_url: str | None
    relevant_experience: str | None
    collaboration_type: str
    motivation: str
    current_learning: str
    deadline_response: str
    communication: str
    feedback_response: str
    teamwork_example: str
    collaboration_conditions: str
    authorship_details: str
    authorship_confirmed: bool
    privacy_consent: bool
    estado: str
    fecha_solicitud: str



class SolicitudEstadoUpdate(BaseModel):
    estado: Literal["ACEPTADA", "RECHAZADA"]