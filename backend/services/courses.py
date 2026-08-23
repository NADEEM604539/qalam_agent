from src.backend.database.database import SessionLocal
from src.backend.web_scraping.playwright_get_courses import get_enrolled_courses
from sqlalchemy import text
from fastapi import HTTPException
from playwright.async_api import Page
from src.backend.web_scraping.playwright_fetch_results import fetch_course_result
import asyncio
import json


async def update_and_fetch_courses(email:str, password:str):
    enrolled_courses = await get_enrolled_courses(email=email, password=password)
    try:
        db = SessionLocal()
        query = text("""SELECT id FROM users 
        WHERE email=:email
""")
        user= await db.execute(query, {
            "email":email
        })
        user_details = user.mappings().fetchone()
        query = text("""SELECT course_id FROM courses
        WHERE user_id=:user_id
""")
        db_courses = await db.execute(query, {
                    "user_id":user_details["id"]
                })
        courses = db_courses.mappings().fetchall()
        db_course_ids = [
            course["course_id"]
            for course in courses
        ]
        for enrolled_course in enrolled_courses:
            if enrolled_course["course_id"] not in db_course_ids:
                query = text("""
                    INSERT INTO courses (
                        course_id,
                        user_id,
                        course_name,
                        course_teacher
                    )
                    VALUES (
                        :course_id,
                        :user_id,
                        :course_name,
                        :course_teacher
                    )
                    """)
                await db.execute(
                    query,
                    {
                        "course_id": enrolled_course["course_id"],
                        "user_id": user_details["id"],
                        "course_name": enrolled_course["course_name"],
                        "course_teacher": enrolled_course["teacher"],
                    }
                )

                await db.commit()
        print(enrolled_courses)       
        return enrolled_courses
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"{e}"
        )
    finally:
        if db:
            await db.close()



async def fetch_results(
    course_id: str,
    email: str,
    password:str
):

    db = SessionLocal()

    try:

        # ---------------------------------------------
        # 1. Get user
        # ---------------------------------------------

        query = text("""
            SELECT id
            FROM users
            WHERE email = :email
        """)

        result = await db.execute(
            query,
            {
                "email": email
            }
        )

        user = result.mappings().fetchone()

        if not user:
            raise Exception(
                f"User not found: {email}"
            )

        user_id = user["id"]

        # ---------------------------------------------
        # 2. Fetch latest result from Qalam
        # ---------------------------------------------

        latest_result = await fetch_course_result(
            course_id=course_id,
            email=email,
            password=password
        )

        # ---------------------------------------------
        # 3. Convert latest result to JSON
        # ---------------------------------------------

        json_data = json.dumps(
            latest_result,
            indent=4,
            ensure_ascii=False
        )

        # ---------------------------------------------
        # 4. Check if marks history exists
        # ---------------------------------------------

        query = text("""
            SELECT id, marks_data
            FROM marks_history
            WHERE user_id = :user_id
              AND course_id = :course_id
            LIMIT 1
        """)

        result = await db.execute(
            query,
            {
                "user_id": user_id,
                "course_id": course_id
            }
        )

        existing_record = result.mappings().fetchone()

        # ---------------------------------------------
        # 5. If no history exists -> INSERT
        # ---------------------------------------------

        if existing_record is None:

            query = text("""
                INSERT INTO marks_history (
                    user_id,
                    course_id,
                    marks_data
                )
                VALUES (
                    :user_id,
                    :course_id,
                    :marks_data
                )
            """)

            await db.execute(
                query,
                {
                    "user_id": user_id,
                    "course_id": course_id,
                    "marks_data": json_data
                }
            )

            await db.commit()

            return {
                "status": "created",
                "changed": True,
                "course_id": course_id,
                "data": latest_result
            }

        # ---------------------------------------------
        # 6. Existing history -> get old JSON
        # ---------------------------------------------

        old_data = existing_record["marks_data"]

        # MySQL JSON can be returned as a string
        # or already decoded depending on the driver.

        if isinstance(old_data, str):

            old_data = json.loads(old_data)

        # ---------------------------------------------
        # 7. Compare old data with latest data
        # ---------------------------------------------

        if old_data == latest_result:

            # Nothing changed
            return {
                "status": "unchanged",
                "changed": False,
                "course_id": course_id,
                "data": latest_result
            }

        # ---------------------------------------------
        # 8. Data changed -> UPDATE
        # ---------------------------------------------

        query = text("""
            UPDATE marks_history
            SET marks_data = :marks_data
            WHERE id = :id
        """)

        await db.execute(
            query,
            {
                "marks_data": json_data,
                "id": existing_record["id"]
            }
        )

        await db.commit()

        return {
            "status": "updated",
            "changed": True,
            "course_id": course_id,
            "data": latest_result,
            "previous_data":old_data
        }

    except Exception:

        await db.rollback()

        raise

    finally:

        await db.close()


if __name__== "__main__":   
    asyncio.run(fetch_results(email="mtariq.bscs24seecs",course_id="2235185"))

    