
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
    picture: Optional[str] = None
    rol: RoleEnum


class RoleUpdateRequest(BaseModel):
    email: str
    nuevo_rol: RoleEnum


# ==================================================
# DATOS DEL CANDIDATO
# ==================================================

class CandidateData(BaseModel):
    display_name: str
    roblox_username: str
    email: str
    discord_username: str


# ==================================================
# PERFIL PROFESIONAL
# ==================================================

class ProfileData(BaseModel):
    position: str
    secondary_positions: Optional[str] = None
    experience_level: str
    timezone: str
    weekly_hours: int = Field(ge=0)

    unavailable_times: Optional[str] = None
    tools: Optional[str] = None
    portfolio_url: Optional[str] = None
    relevant_experience: Optional[str] = None

    collaboration_type: str


# ==================================================
# RESPUESTAS DEL FORMULARIO
# ==================================================

class AnswersData(BaseModel):
    motivation: str
    current_learning: str
    deadline_response: str
    communication: str
    feedback_response: str
    teamwork_example: str
    collaboration_conditions: str
    authorship_details: str


# ==================================================
# DECLARACIONES
# ==================================================

class DeclarationsData(BaseModel):
    authorship_confirmed: bool
    privacy_consent: bool


# ==================================================
# CREAR UNA SOLICITUD
# ==================================================

class SolicitudTrabajoCrear(BaseModel):
    candidate: CandidateData
    profile: ProfileData
    answers: AnswersData
    declarations: DeclarationsData


# ==================================================
# CAMBIAR EL ESTADO
# ==================================================

class SolicitudEstadoActualizar(BaseModel):
    estado: str


# ==================================================
# RESPUESTA DE LA API
# ==================================================

class SolicitudTrabajo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int

    candidate: CandidateData
    profile: ProfileData
    answers: AnswersData
    declarations: DeclarationsData

    estado: str
    fecha_solicitud: datetime
