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
    def role_checker(
        user: dict = Depends(get_current_user),
    ) -> dict:
        if user["rol"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta operación.",
            )

        return user

    return role_checker