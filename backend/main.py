
import os
from dotenv import load_dotenv

# Cargar las variables antes de importar los módulos de la API
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from auth import router as auth_router


app = FastAPI(title="Dream Projects Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dreamprojectsstudio.nanadev.online",
        "http://localhost:4321",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)

# Sesión temporal firmada que Authlib utiliza para el estado OAuth.
# No es la sesión de usuario almacenada en MySQL.
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["OAUTH_STATE_SECRET"],
    session_cookie="oauth_state",
    max_age=600,
    same_site="lax",
    https_only=(
        os.environ.get("COOKIE_SECURE", "true").lower() == "true"
    ),
)

app.include_router(auth_router)


@app.get("/")
def inicio():
    return {"mensaje": "API de Dream Projects Studio funcionando"}
