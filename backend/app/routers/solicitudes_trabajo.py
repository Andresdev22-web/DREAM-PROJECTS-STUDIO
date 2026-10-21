
from fastapi import APIRouter, HTTPException

from app.database import get_db_connection
from app.models import SolicitudTrabajoCrear


router = APIRouter(
    prefix="/solicitudes-trabajo",
    tags=["Solicitudes de trabajo"],
)


# ==================================================
# CONVERTIR LOS DATOS DE SQLITE A JSON
# ==================================================

def convertir_solicitud(fila):
    datos = dict(fila)

    return {
        "id": datos["id"],

        "candidate": {
            "display_name": datos["display_name"],
            "roblox_username": datos["roblox_username"],
            "email": datos["email"],
            "discord_username": datos["discord_username"],
        },

        "profile": {
            "position": datos["position"],
            "secondary_positions": datos["secondary_positions"],
            "experience_level": datos["experience_level"],
            "timezone": datos["timezone"],
            "weekly_hours": datos["weekly_hours"],
            "unavailable_times": datos["unavailable_times"],
            "tools": datos["tools"],
            "portfolio_url": datos["portfolio_url"],
            "relevant_experience": datos["relevant_experience"],
            "collaboration_type": datos["collaboration_type"],
        },

        "answers": {
            "motivation": datos["motivation"],
            "current_learning": datos["current_learning"],
            "deadline_response": datos["deadline_response"],
            "communication": datos["communication"],
            "feedback_response": datos["feedback_response"],
            "teamwork_example": datos["teamwork_example"],
            "collaboration_conditions": datos["collaboration_conditions"],
            "authorship_details": datos["authorship_details"],
        },

        "declarations": {
            "authorship_confirmed": bool(
                datos["authorship_confirmed"]
            ),
            "privacy_consent": bool(datos["privacy_consent"]),
        },

        "estado": datos["estado"],
        "fecha_solicitud": datos["fecha_solicitud"],
    }


# ==================================================
# 1. GUARDAR UNA SOLICITUD
# POST /solicitudes-trabajo/
# ==================================================

@router.post("/", status_code=201)
def crear_solicitud(payload: SolicitudTrabajoCrear):
    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        usuario_id = payload.usuario_id
        candidate = payload.candidate
        profile = payload.profile
        answers = payload.answers
        declarations = payload.declarations

        # Validaciones básicas del formulario.
        if not declarations.authorship_confirmed:
            raise HTTPException(
                status_code=400,
                detail="Debes confirmar la autoría de la información.",
            )

        if not declarations.privacy_consent:
            raise HTTPException(
                status_code=400,
                detail="Debes aceptar el consentimiento de privacidad.",
            )

        # Guardar la solicitud asociada al usuario indicado.
        cursor.execute(
            """
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
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            )
            """,
            (
                usuario_id,
                candidate.display_name,
                candidate.roblox_username,
                candidate.email,
                candidate.discord_username,
                profile.position,
                profile.secondary_positions,
                profile.experience_level,
                profile.timezone,
                profile.weekly_hours,
                profile.unavailable_times,
                profile.tools,
                profile.portfolio_url,
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
            ),
        )

        # Obtener el ID generado automáticamente por SQLite.
        solicitud_id = cursor.lastrowid
        conn.commit()

        # Consultar la solicitud recién creada.
        cursor.execute(
            """
            SELECT *
            FROM solicitudes_trabajo
            WHERE id = ?
            """,
            (solicitud_id,),
        )

        return convertir_solicitud(cursor.fetchone())

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ==================================================
# 2. VER TODAS LAS SOLICITUDES
# GET /solicitudes-trabajo/
# ==================================================

@router.get("/")
def listar_solicitudes():
    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM solicitudes_trabajo
            ORDER BY fecha_solicitud DESC, id DESC
            """
        )

        filas = cursor.fetchall()

        return [
            convertir_solicitud(fila)
            for fila in filas
        ]

    finally:
        conn.close()


# ==================================================
# 3. ELIMINAR UNA SOLICITUD POR ID
# DELETE /solicitudes-trabajo/{solicitud_id}
# ==================================================

@router.delete("/{solicitud_id}")
def eliminar_solicitud(solicitud_id: int):
    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM solicitudes_trabajo
            WHERE id = ?
            """,
            (solicitud_id,),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="No existe una solicitud con ese ID.",
            )

        conn.commit()

        return {
            "mensaje": "Solicitud eliminada correctamente.",
            "id": solicitud_id,
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
