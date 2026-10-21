
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import DB_NAME
from app.models.models import SolicitudCreate, SolicitudResponse , SolicitudEstadoUpdate
from app.dependencies.auth import get_current_user, require_role

router = APIRouter(
    prefix="/solicitudes",
    tags=["Solicitudes de trabajo"],
)


def get_user_id(user):
    """Obtiene el ID del usuario autenticado."""
    if isinstance(user, dict):
        return user["id"]

    return user.id


def row_to_response(row):
    """Convierte una fila SQLite al formato de respuesta."""
    result = dict(row)
    result["authorship_confirmed"] = bool(
        result["authorship_confirmed"]
    )
    result["privacy_consent"] = bool(result["privacy_consent"])
    return result


@router.post(
    "/",
    response_model=SolicitudResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_solicitud(
    payload: SolicitudCreate,
    current_user=Depends(get_current_user),
):
    usuario_id = get_user_id(current_user)

    if not payload.declarations.authorship_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Debes confirmar la autoría de la información.",
        )

    if not payload.declarations.privacy_consent:
        raise HTTPException(
            status_code=400,
            detail="Debes aceptar el tratamiento de tus datos.",
        )

    candidate = payload.candidate
    profile = payload.profile
    answers = payload.answers
    declarations = payload.declarations

    query = """
        INSERT INTO solicitudes_trabajo (
            usuario_id,
            display_name,
            roblox_username,
            email,
            discord_username,
            position,
            secondary_positions,
            experience_level,
            timezone,
            weekly_hours,
            unavailable_times,
            tools,
            portfolio_url,
            relevant_experience,
            collaboration_type,
            motivation,
            current_learning,
            deadline_response,
            communication,
            feedback_response,
            teamwork_example,
            collaboration_conditions,
            authorship_details,
            authorship_confirmed,
            privacy_consent
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """

    values = (
        usuario_id,
        candidate.display_name,
        candidate.roblox_username,
        str(candidate.email),
        candidate.discord_username,
        profile.position,
        profile.secondary_positions,
        profile.experience_level,
        profile.timezone,
        profile.weekly_hours,
        profile.unavailable_times,
        profile.tools,
        str(profile.portfolio_url) if profile.portfolio_url else None,
        profile.relevant_experience,
        profile.collaboration_type,
        answers.motivation,
        answers.current_learning,
        answers.deadline_response,
        answers.communication,
        answers.feedback_response,
        answers.teamwork_example,
        answers.collaboration_conditions,
        answers.authorship_details,
        int(declarations.authorship_confirmed),
        int(declarations.privacy_consent),
    )

    conn = None

    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        cursor = conn.execute(query, values)
        solicitud_id = cursor.lastrowid
        conn.commit()

        row = conn.execute(
            """
            SELECT *
            FROM solicitudes_trabajo
            WHERE id = ?
            """,
            (solicitud_id,),
        ).fetchone()

        return row_to_response(row)

    except sqlite3.IntegrityError as error:
        if conn:
            conn.rollback()

        raise HTTPException(
            status_code=400,
            detail="No se pudo guardar la solicitud. Verifica el usuario asociado.",
        ) from error

    except sqlite3.Error as error:
        if conn:
            conn.rollback()

        raise HTTPException(
            status_code=500,
            detail="Error al guardar la solicitud.",
        ) from error

    finally:
        if conn:
            conn.close()


@router.get(
    "/",
    response_model=list[SolicitudResponse],
)
def listar_solicitudes(
    admin=Depends(require_role("ADMINISTRADOR")),
):
    """Lista todas las solicitudes. Solo para administradores."""
    conn = None

    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        rows = conn.execute(
            """
            SELECT *
            FROM solicitudes_trabajo
            ORDER BY fecha_solicitud DESC, id DESC
            """
        ).fetchall()

        return [row_to_response(row) for row in rows]

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar las solicitudes.",
        ) from error

    finally:
        if conn:
            conn.close()



# borrar luego
@router.get(
    "/abierta",
    response_model=list[SolicitudResponse],
)
def listar_solicitudes():
    """Lista todas las solicitudes de trabajo."""
    conn = None

    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        rows = conn.execute(
            """
            SELECT *
            FROM solicitudes_trabajo
            ORDER BY fecha_solicitud DESC, id DESC
            """
        ).fetchall()

        return [row_to_response(row) for row in rows]

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar las solicitudes.",
        ) from error

    finally:
        if conn:
            conn.close()




@router.patch(
    "/{solicitud_id}/estado",
    response_model=SolicitudResponse,
)
def actualizar_estado_solicitud(
    solicitud_id: int,
    datos: SolicitudEstadoUpdate,
    admin=Depends(require_role("ADMINISTRADOR")),
):
    """Acepta o rechaza una solicitud pendiente. Solo administradores."""

    conn = None

    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        # 1. Buscar la solicitud.
        solicitud = conn.execute(
            """
            SELECT *
            FROM solicitudes_trabajo
            WHERE id = ?
            """,
            (solicitud_id,),
        ).fetchone()

        if solicitud is None:
            raise HTTPException(
                status_code=404,
                detail="La solicitud no existe.",
            )

        # 2. Solo permitir modificar solicitudes pendientes.
        if solicitud["estado"].upper() != "PENDIENTE":
            raise HTTPException(
                status_code=409,
                detail="Esta solicitud ya fue gestionada.",
            )

        # 3. Guardar el nuevo estado.
        conn.execute(
            """
            UPDATE solicitudes_trabajo
            SET estado = ?
            WHERE id = ?
            """,
            (datos.estado, solicitud_id),
        )
        conn.commit()

        # 4. Devolver la solicitud actualizada.
        solicitud_actualizada = conn.execute(
            """
            SELECT *
            FROM solicitudes_trabajo
            WHERE id = ?
            """,
            (solicitud_id,),
        ).fetchone()

        return row_to_response(solicitud_actualizada)

    except HTTPException:
        raise

    except sqlite3.Error as error:
        if conn:
            conn.rollback()

        raise HTTPException(
            status_code=500,
            detail="Error al actualizar el estado de la solicitud.",
        ) from error

    finally:
        if conn:
            conn.close()





@router.get(
    "/{solicitud_id}",
    response_model=SolicitudResponse,
)
def obtener_solicitud(
    solicitud_id: int,
    admin=Depends(require_role("ADMINISTRADOR")),
):
    """Consulta una solicitud concreta. Solo para administradores."""
    conn = None

    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row

        row = conn.execute(
            """
            SELECT *
            FROM solicitudes_trabajo
            WHERE id = ?
            """,
            (solicitud_id,),
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Solicitud no encontrada.",
            )

        return row_to_response(row)

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar la solicitud.",
        ) from error

    finally:
        if conn:
            conn.close()
