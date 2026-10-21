from fastapi import APIRouter, Depends, HTTPException

from app.models import GoogleLoginRequest, TokenResponse, UserResponse
from app.services.auth_service import authenticate_google_user
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/google", response_model=TokenResponse)
def login_google(payload: GoogleLoginRequest):
    try:
        return authenticate_google_user(payload.token)

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="No se pudo autenticar con Google.",
        )


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    user: dict = Depends(get_current_user),
):
    return user