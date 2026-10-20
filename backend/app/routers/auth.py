from fastapi import APIRouter, HTTPException, Header
from google.oauth2 import id_token
from google.auth.transport import requests
from app.config import GOOGLE_CLIENT_ID
from app.models import GoogleLoginRequest, UserResponse
from app.auth import upsert_google_user, get_current_user_optional

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/google", response_model=UserResponse)
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

@router.get("/me", response_model=UserResponse)
def get_my_profile(authorization: Optional[str] = Header(None)):
    user = get_current_user_optional(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="No se pudo autenticar al usuario. Token ausente o inválido.")
    return user