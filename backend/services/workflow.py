import asyncio
import os
import httpx
from dotenv import load_dotenv

from src.backend.services.courses import update_and_fetch_courses, fetch_results
from src.backend.services.login import get_all_users
from src.backend.LLM.create_marks_change_email import llm_generate_email

load_dotenv()

EMAIL_VERIFICATION_URL = os.getenv("EMAIL_VERIFICATION_URL")
EMAIL_VERIFICATION_API_KEY = os.getenv("EMAIL_VERIFICATION_API_KEY")


async def send_email_verification(email: str, send_to: list[str]):
    async with httpx.AsyncClient() as client:
        payload = {
            "email": email,
            "send_to": send_to
        }

        response = await client.post(
            EMAIL_VERIFICATION_URL,
            headers={
                "email-verification": EMAIL_VERIFICATION_API_KEY
            },
            json=payload,
            timeout=30.0,
        )

        if response.status_code >= 400:
            # Surface the real validation error instead of a bare
            # HTTPStatusError with no detail.
            print(f"[email-service] Sent payload: {payload}")
            print(
                f"[email-service] {response.status_code} error body: "
                f"{response.text}"
            )

        response.raise_for_status()

        return response.json()


async def marks_change_workflow():

    users = await get_all_users()

    for user in users:

        user_email = user.get("email", "<unknown>")

        try:
            active_courses = await update_and_fetch_courses(
                email=user["email"],
                password=user["password"]
            )

        except Exception as e:
            print(f"[skip] Could not fetch courses for {user_email}: {e}")
            continue

        updated_courses_input = []

        for course in active_courses:

            try:
                results = await fetch_results(
                    email=user["email"],
                    password=user["password"],
                    course_id=course["course_id"],
                )

            except Exception as e:
                print(
                    f"[skip] Could not fetch results for {user_email} "
                    f"/ course {course.get('course_id', '<unknown>')}: {e}"
                )
                continue

            if results["status"] == "updated":

                updated_courses_input.append({
                    "course_id": results["course_id"],
                    "data": results["data"],
                    "previous_data": results.get("previous_data"),
                })

        if not updated_courses_input:
            continue

        try:
            email_response = await llm_generate_email(
                updated_courses_input
            )

        except Exception as e:
            print(
                f"[skip] LLM email generation failed for "
                f"{user_email}: {e}"
            )
            continue

        if email_response.marks_changed:

            try:
                print(f"Sending email to {user_email}")
                print(email_response.email_body)

                # NOTE: confirm what user['email'] actually contains before
                # relying on this. If it's already a full address (e.g.
                # 'someone@seecs.edu.pk'), appending the domain again will
                # produce an invalid double-domain address and the email
                # service will reject it with a 422.
                print(f"[debug] raw user['email'] = {user['email']!r}")

                recipient = user["email"]
                if "@" not in recipient:
                    recipient = recipient + "@seecs.edu.pk"
                recipients=[]
                recipients.append(recipient)
                response = await send_email_verification(
                    email=email_response.email_body,
                    send_to=recipients
                )

                print("Email service response:", response)

            except Exception as e:
                print(
                    f"[skip] Failed to send email to "
                    f"{user_email}: {e}"
                )

        else:
            print(
                f"No real new results for {user_email} "
                f"— skipping email."
            )


if __name__ == "__main__":
    asyncio.run(marks_change_workflow())