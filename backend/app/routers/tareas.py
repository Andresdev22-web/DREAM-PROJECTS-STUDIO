from fastapi import APIRouter, Depends

from app.dependencies.auth import require_role

router = APIRouter(prefix="/solicitudes", tags=["Solicitudes"])


@router.get("/")
def listar_solicitudes(
    admin: dict = Depends(require_role("ADMIN")),
):
    # Aquí llamarías al servicio que consulta las solicitudes.
    return {
        "mensaje": "Acceso autorizado",
        "administrador": admin["email"],
    }