from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import List

app = FastAPI(title="API Dream Projects Studio")

# 1. Configuración de CORS
# Permite peticiones desde localhost (pruebas) y desde tu dominio de producción
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "https://dreamprojectsstudioapi.nanadev.online",
    "*"  # Permite cualquier origen durante las pruebas
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Inicializar Base de Datos SQLite
def init_db():
    conn = sqlite3.connect("tareas.db")
    cursor = conn.cursor()
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

# Modelos Pydantic para validar los datos recibidos
class TareaCrear(BaseModel):
    titulo: str

class Tarea(BaseModel):
    id: int
    titulo: str
    completada: bool

# 3. Endpoints de la API

@app.get("/")
def home():
    return {"status": "ok", "mensaje": "API de prueba funcionando"}

@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas():
    conn = sqlite3.connect("tareas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, completada FROM tareas")
    filas = cursor.fetchall()
    conn.close()
    
    return [{"id": fila[0], "titulo": fila[1], "completada": bool(fila[2])} for fila in filas]

@app.post("/tareas", response_model=Tarea)
def crear_tarea(tarea: TareaCrear):
    conn = sqlite3.connect("tareas.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tareas (titulo, completada) VALUES (?, ?)", (tarea.titulo, False))
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    return {"id": tarea_id, "titulo": tarea.titulo, "completada": False}