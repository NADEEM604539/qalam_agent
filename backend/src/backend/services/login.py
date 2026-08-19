from backend.DTO.login import Login_request
from backend.database.database import SessionLocal
from fastapi import HTTPException
from sqlalchemy import text
from backend.services.security import encrypt_password, verify_password

async def login(request: Login_request):
    db = SessionLocal
    try:
        query = text("""SELECT id, password_hash FROM users
        where email=:email

    """)
        user = await db.execute(query,{
            "email":request.email
        }).mappings().fetchone()



    
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail=f"{e}"
        )
    finally:
        await db.close()


async def register(request: Login_request):
    db = SessionLocal
    try:
        query = text("""
""")
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail=f"{e}"
        )
    finally:
        await db.close()


async def get_user(email:str):
    db = SessionLocal()
    try:
        query = text("""SELECT id FROM users
        WHERE email=:email
""")

        user = await db.execute(query,{
            "email": email
        })

        return user.mappings().fetchone()

    except Exception as e:
        print(f"Database error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"{e}"
        )

    finally:
        await db.close()