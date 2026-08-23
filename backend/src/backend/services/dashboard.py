from backend.database.database import SessionLocal
from sqlalchemy import text
import json


def _parse_marks(raw) -> list:
    """
    Safely turn whatever the DB returns into a plain list of
    section objects that the frontend can iterate over directly.

    The DB may store marks as:
      - A JSON string  → parse once, then extract sections
      - A dict already → extract sections directly
      - None           → return []
    """
    if raw is None:
        return []

    # MySQL asyncmy driver sometimes returns JSON columns as strings.
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return []

    # raw is now a dict: { "sections": [...], "course_id": "..." }
    if isinstance(raw, dict):
        sections = raw.get("sections") or []
        return sections

    # Already a list (shouldn't happen, but be safe)
    if isinstance(raw, list):
        return raw

    return []


async def get_dashboard(email: str):
    db = SessionLocal()

    try:
        # Pull from BOTH courses.marks (fast, always present) AND
        # marks_history.marks_data (latest scraped snapshot).
        # Prefer marks_history when it exists; fall back to courses.marks.
        query = text("""
            SELECT
                u.id            AS user_id,
                u.email,
                u.is_active,

                c.course_id,
                c.course_name,
                c.course_teacher,
                c.marks         AS course_marks,

                mh.marks_data   AS history_marks,
                mh.created_at   AS marks_updated_at

            FROM users u

            LEFT JOIN courses c
                ON c.user_id = u.id

            LEFT JOIN marks_history mh
                ON mh.course_id = c.course_id
                AND mh.user_id  = u.id
                AND mh.id = (
                    SELECT MAX(mh2.id)
                    FROM marks_history mh2
                    WHERE mh2.course_id = c.course_id
                      AND mh2.user_id   = u.id
                )

            WHERE u.email = :email
            ORDER BY c.course_name;
        """)

        result = await db.execute(query, {"email": email})
        rows = result.mappings().all()

        if not rows:
            return None

        dashboard = {
            "user": {
                "id":        rows[0]["user_id"],
                "email":     rows[0]["email"],
                "is_active": rows[0]["is_active"],
            },
            "courses": [],
        }

        for row in rows:
            if row["course_id"] is None:
                continue

            # Prefer the latest marks_history snapshot; fall back to
            # the marks stored directly on the courses row.
            raw = row["history_marks"] if row["history_marks"] is not None else row["course_marks"]

            sections = _parse_marks(raw)

            dashboard["courses"].append({
                "course_id":        row["course_id"],
                "course_name":      row["course_name"],
                "course_teacher":   row["course_teacher"],
                "marks":            sections,
                "marks_updated_at": (
                    row["marks_updated_at"].isoformat()
                    if row["marks_updated_at"] else None
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
            WHERE email   = :email
        """)

        result = await db.execute(query, {"email": email, "status": status})
        await db.commit()

        if result.rowcount == 0:
            return None

        return {"email": email, "is_active": status}

    except Exception:
        await db.rollback()
        raise

    finally:
        await db.close()
