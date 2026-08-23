from src.backend.database.database import SessionLocal
from sqlalchemy import text
import json


def _parse_marks(raw) -> list:
    """
    Safely convert marks_data from the database into
    a list of sections for the frontend.
    """

    if raw is None:
        return []

    # JSON column may come back as a string
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return []

    # Expected structure:
    # {
    #     "course_id": "...",
    #     "sections": [...]
    # }
    if isinstance(raw, dict):
        return raw.get("sections") or []

    # Safety fallback
    if isinstance(raw, list):
        return raw

    return []


async def get_dashboard(email: str):
    db = SessionLocal()

    try:
        query = text("""
            SELECT
                u.id              AS user_id,
                u.email,
                u.is_active,

                c.course_id,
                c.course_name,
                c.course_teacher,

                mh.marks_data     AS marks_data,
                mh.created_at     AS marks_updated_at

            FROM users u

            LEFT JOIN courses c
                ON c.user_id = u.id

            LEFT JOIN marks_history mh
                ON mh.course_id = c.course_id
                AND mh.user_id = u.id
                AND mh.id = (
                    SELECT MAX(mh2.id)
                    FROM marks_history mh2
                    WHERE mh2.course_id = c.course_id
                      AND mh2.user_id = u.id
                )

            WHERE u.email = :email

            ORDER BY c.course_name;
        """)

        result = await db.execute(
            query,
            {"email": email}
        )

        rows = result.mappings().all()

        if not rows:
            return None

        dashboard = {
            "user": {
                "id": rows[0]["user_id"],
                "email": rows[0]["email"],
                "is_active": rows[0]["is_active"],
            },
            "courses": []
        }

        for row in rows:

            # User may exist without any courses
            if row["course_id"] is None:
                continue

            sections = _parse_marks(
                row["marks_data"]
            )

            dashboard["courses"].append({
                "course_id": row["course_id"],
                "course_name": row["course_name"],
                "course_teacher": row["course_teacher"],
                "marks": sections,
                "marks_updated_at": (
                    row["marks_updated_at"].isoformat()
                    if row["marks_updated_at"]
                    else None
                ),
            })

        return dashboard

    finally:
        await db.close()


async def toggle_status(email: str, status: bool):
    db = SessionLocal()

    try:
        query = text("""
            UPDATE users
            SET is_active = :status
            WHERE email = :email
        """)

        result = await db.execute(
            query,
            {
                "email": email,
                "status": status
            }
        )

        await db.commit()

        if result.rowcount == 0:
            return None

        return {
            "email": email,
            "is_active": status
        }

    except Exception:
        await db.rollback()
        raise

    finally:
        await db.close()