
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import DB_NAME
from app.models.models import (
    SolicitudCreate,
    SolicitudResponse,
    SolicitudEstadoUpdate,
    ExamenResultadoUpdate,
)
from app.dependencies.auth import get_current_user, require_role


# ============================================================
# CONFIGURACIÓN DEL ROUTER
# Todas las rutas de este archivo comienzan con /solicitudes
# ============================================================

router = APIRouter(
    prefix="/solicitudes",
    tags=["Solicitudes de trabajo"],
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def get_user_id(user):
    """Obtiene el ID del usuario autenticado."""

    if isinstance(user, dict):
        return user["id"]

    return user.id


def row_to_response(row):
    """Convierte una fila SQLite en un diccionario compatible
    con el modelo SolicitudResponse.
    """

    result = dict(row)

    # SQLite almacena estos valores booleanos como 0 o 1.
    result["authorship_confirmed"] = bool(
        result["authorship_confirmed"]
    )
    result["privacy_consent"] = bool(
        result["privacy_consent"]
    )
    result["examen_completado"] = bool(
        result["examen_completado"]
    )

    return result


# ============================================================
# RUTA 1: CREAR UNA SOLICITUD DE TRABAJO
# Método: POST
# Ruta: /solicitudes/
# Acceso: usuario autenticado
#
# Recibe los datos del candidato, su perfil, sus respuestas
# y sus declaraciones.
#
# El examen no se registra aquí: queda pendiente por defecto.
# ============================================================

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

    # Comprobar las declaraciones obligatorias.
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

    # Insertar únicamente los datos de la solicitud.
    # El examen utiliza los valores DEFAULT definidos en SQLite.
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
        (
            str(profile.portfolio_url)
            if profile.portfolio_url
            else None
        ),
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

        # Recuperar la solicitud recién creada.
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
            detail=(
                "No se pudo guardar la solicitud. "
                "Verifica el usuario asociado."
            ),
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


# ============================================================
# RUTA 2: LISTAR TODAS LAS SOLICITUDES
# Método: GET
# Ruta: /solicitudes/
# Acceso: ADMINISTRADOR
#
# Permite al administrador ver las solicitudes recibidas,
# incluidos los estados y los resultados de los exámenes.
# ============================================================

@router.get(
    "/",
    response_model=list[SolicitudResponse],
)
def listar_solicitudes(
    admin=Depends(require_role("ADMINISTRADOR")),
):
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


# ============================================================
# RUTA 3: LISTAR SOLICITUDES SIN RESTRICCIÓN DE ROL
# Método: GET
# Ruta: /solicitudes/abierta
#
# RUTA TEMPORAL DE PRUEBA.
# No utiliza require_role ni get_current_user.
#
# IMPORTANTE: elimina esta ruta o añade autenticación antes
# de producción si las solicitudes contienen datos personales.
# ============================================================

@router.get(
    "/abierta",
    response_model=list[SolicitudResponse],
)
def listar_solicitudes_abierta():
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


# ============================================================
# RUTA 4: ACEPTAR O RECHAZAR UNA SOLICITUD
# Método: PATCH
# Ruta: /solicitudes/{solicitud_id}/estado
# Acceso: ADMINISTRADOR
#
# Recibe el ID por la URL y el nuevo estado en el JSON.
# Solo permite cambiar solicitudes que sigan pendientes.
# ============================================================

@router.patch(
    "/{solicitud_id}/estado",
    response_model=SolicitudResponse,
)
def actualizar_estado_solicitud(
    solicitud_id: int,
    datos: SolicitudEstadoUpdate,
    admin=Depends(require_role("ADMINISTRADOR")),
):
    conn = None

    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        # Buscar la solicitud.
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

        # Comprobar que aún esté pendiente.
        if solicitud["estado"].lower() != "pendiente":
            raise HTTPException(
                status_code=409,
                detail="Esta solicitud ya fue gestionada.",
            )

        # Guardar el estado utilizando el mismo formato
        # en minúsculas que el DEFAULT de la tabla SQLite.
        nuevo_estado = datos.estado.lower()

        if nuevo_estado not in ("aceptada", "rechazada"):
            raise HTTPException(
                status_code=422,
                detail="El estado debe ser ACEPTADA o RECHAZADA.",
            )

        conn.execute(
            """
            UPDATE solicitudes_trabajo
            SET estado = ?
            WHERE id = ?
            """,
            (nuevo_estado, solicitud_id),
        )

        conn.commit()

        # Devolver la solicitud actualizada.
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


# ============================================================
# RUTA 5: REGISTRAR EL RESULTADO DEL EXAMEN
# Método: PATCH
# Ruta: /solicitudes/{solicitud_id}/examen
# Acceso: ADMINISTRADOR
#
# Se utiliza más adelante, cuando el candidato haya terminado
# su examen.
#
# Recibe:
#   - examen_completado
#   - puntaje_examen
#
# El ID de la solicitud se envía por la URL.
# No se vuelven a enviar los datos personales del candidato.
# ============================================================

@router.patch(
    "/{solicitud_id}/examen",
    response_model=SolicitudResponse,
)
def actualizar_resultado_examen(
    solicitud_id: int,
    datos: ExamenResultadoUpdate,
    admin=Depends(require_role("ADMINISTRADOR")),
):
    conn = None

    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        # Comprobar que la solicitud exista.
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

        # Evitar registrar dos veces el mismo examen.
        if solicitud["examen_completado"]:
            raise HTTPException(
                status_code=409,
                detail="El examen de esta solicitud ya fue registrado.",
            )

        # No permitir marcar el examen como incompleto
        # al mismo tiempo que se registra una nota.
        if not datos.examen_completado:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Para registrar un resultado, "
                    "el examen debe estar completado."
                ),
            )

        # Guardar el resultado y la fecha de finalización.
        conn.execute(
            """
            UPDATE solicitudes_trabajo
            SET
                examen_completado = 1,
                puntaje_examen = ?,
                fecha_completado_examen = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                datos.puntaje_examen,
                solicitud_id,
            ),
        )

        conn.commit()

        # Devolver la solicitud con el resultado actualizado.
        resultado = conn.execute(
            """
            SELECT *
            FROM solicitudes_trabajo
            WHERE id = ?
            """,
            (solicitud_id,),
        ).fetchone()

        return row_to_response(resultado)

    except HTTPException:
        raise

    except sqlite3.Error as error:
        if conn:
            conn.rollback()

        raise HTTPException(
            status_code=500,
            detail="Error al guardar el resultado del examen.",
        ) from error

    finally:
        if conn:
            conn.close()


# ============================================================
# RUTA 6: CONSULTAR UNA SOLICITUD POR SU ID
# Método: GET
# Ruta: /solicitudes/{solicitud_id}
# Acceso: ADMINISTRADOR
#
# Devuelve una solicitud específica con todos sus datos,
# incluidos el estado del proceso y el resultado del examen.
# ============================================================

@router.get(
    "/{solicitud_id}",
    response_model=SolicitudResponse,
)
def obtener_solicitud(
    solicitud_id: int,
    admin=Depends(require_role("ADMINISTRADOR")),
):
    conn = None

    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

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

    except HTTPException:
        raise

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar la solicitud.",
        ) from error

    finally:
        if conn:
            conn.close()




# ============================================================
# RUTA: CONSULTAR MI SOLICITUD DE TRABAJO
# Método: GET
# Ruta: /solicitudes/mia
# Acceso: usuario autenticado
#
# Devuelve únicamente la solicitud del usuario de la sesión.
# ============================================================

@router.get(
    "/mia",
    response_model=SolicitudResponse,
)
def obtener_mi_solicitud(
    current_user=Depends(get_current_user),
):
    usuario_id = get_user_id(current_user)
    conn = None

    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row

        row = conn.execute(
            """
            SELECT *
            FROM solicitudes_trabajo
            WHERE usuario_id = ?
            ORDER BY fecha_solicitud DESC, id DESC
            LIMIT 1
            """,
            (usuario_id,),
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Todavía no has enviado una solicitud de trabajo.",
            )

        return row_to_response(row)

    except HTTPException:
        raise

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar tu solicitud.",
        ) from error

    finally:
        if conn:
            conn.close()
