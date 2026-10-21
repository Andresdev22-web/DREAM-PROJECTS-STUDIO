from typing import Optional, Callable

import jwt
from fastapi import Header, HTTPException, Depends, status

from app.config import JWT_SECRET_KEY, JWT_ALGORITHM
from app.database import get_db_connection
from app.services.auth_service import get_user_by_id


def get_current_user(
    authorization: Optional[str] = Header(None),
) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el token de autenticación.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de autenticación inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp"]},
        )

        user_id = int(payload["sub"])

    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario asociado al token ya no existe.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(required_role: str) -> Callable:
    print("\n" + "=" * 60)
    print("[AUTH DEBUG] Creando verificador de rol")
    print(f"[AUTH DEBUG] Rol requerido: {required_role!r}")
    print("=" * 60)

    def role_checker(
        user: dict = Depends(get_current_user),
    ) -> dict:
        print("\n" + "=" * 60)
        print("[AUTH DEBUG] EJECUTANDO VERIFICACIÓN DE ROL")
        print("-" * 60)

        print(f"[AUTH DEBUG] Rol requerido: {required_role!r}")
        print(f"[AUTH DEBUG] Tipo de usuario: {type(user).__name__}")
        print(f"[AUTH DEBUG] Usuario recibido: {user!r}")

        if not isinstance(user, dict):
            print("[AUTH DEBUG] ERROR: El usuario no es un diccionario.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al obtener el usuario.",
            )

        print(f"[AUTH DEBUG] ID: {user.get('id')!r}")
        print(f"[AUTH DEBUG] Email: {user.get('email')!r}")
        print(f"[AUTH DEBUG] Nombre: {user.get('nombre')!r}")
        print(f"[AUTH DEBUG] Rol del usuario: {user.get('rol')!r}")
        print(f"[AUTH DEBUG] Rol esperado: {required_role!r}")

        user_role = user.get("rol")

        if user_role != required_role:
            print("[AUTH DEBUG] RESULTADO: ACCESO DENEGADO")
            print(
                f"[AUTH DEBUG] Comparación: "
                f"{user_role!r} != {required_role!r}"
            )
            print("=" * 60 + "\n")

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "mensaje": "No tienes permisos para realizar esta operación.",
                    "rol_requerido": required_role,
                    "rol_usuario": user_role,
                    "usuario_id": user.get("id"),
                    "usuario_email": user.get("email"),
                },
            )

        print("[AUTH DEBUG] RESULTADO: ACCESO AUTORIZADO")
        print("=" * 60 + "\n")

        return user

    return role_checker