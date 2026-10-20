from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import auth, admin, tareas

app = FastAPI(
    title="API Dream Projects Studio - Modular",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar Base de Datos al arrancar
init_db()

# Registrar los Routers modularizados
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(tareas.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "API modular funcionando correctamente"}