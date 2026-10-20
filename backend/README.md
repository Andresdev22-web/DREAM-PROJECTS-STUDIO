backend/
├── app/
│   ├── __init__.py               # Indica que 'app' es un paquete de Python.
│   ├── config.py                 # [CONFIGURACIÓN] Carga variables de entorno (.env) como CLIENT_ID.
│   ├── database.py               # [BASE DE DATOS] Inicializa la conexión SQLite y crea las tablas automáticamente.
│   ├── models.py                 # [ESQUEMAS] Define las estructuras de datos con Pydantic (Validadores de entrada/salida) y Enums.
│   ├── auth.py                   # [SEGURIDAD] Lógica pura para verificar tokens de Google y buscar/crear usuarios.
│   └── routers/
│       ├── __init__.py
│       ├── auth.py               # [RUTAS] Endpoints para login con Google (/auth/google) y perfil (/auth/me).
│       ├── admin.py              # [RUTAS] Endpoints para listar, actualizar roles o eliminar usuarios (/admin/...).
│       └── tareas.py             # [RUTAS] Endpoints de prueba, simulación de permisos y CRUD de tareas (/tareas, /rutas/...).
├── main.py                       # [NÚCLEO] Crea la app FastAPI, añade CORS, inicializa la DB y unifica todos los routers.
├── requirements.txt              # [DEPENDENCIAS] Librerías de Python necesarias para que corra el proyecto.
├── .env                          # [SECRETOS] Almacena credenciales privadas que no deben subirse al repositorio público.
├── Dockerfile                    # [CONTENEDOR] Instrucciones para empaquetar la app de Python.
└── docker-compose.yml            # [ORQUESTADOR] Configura el contenedor, red de Traefik y lectura del .env.