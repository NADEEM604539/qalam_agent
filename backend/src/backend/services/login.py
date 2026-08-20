from backend.DTO.login import Login_request
from backend.database.database import SessionLocal
from fastapi import HTTPException
from sqlalchemy import text
from backend.services.security import encrypt_password, decrypt_password
from backend.services.jwt import create_access_token
from backend.DTO.login import Payload

async def login(request: Login_request):
    db = SessionLocal()
    payload = Payload(
            email=request.email
        )
    access_token = create_access_token(data=payload)
    try:
        query = text("""SELECT id, password_hash FROM users
        where email=:email

    """)
        user = await db.execute(query,{
            "email":request.email
        })
        user_details = user.mappings().fetchone()
        decrypted_password = decrypt_password(user_details["password_hash"])
        if decrypted_password!= request.password:
            encrypted_password=encrypt_password(request.password)
            query = text("""UPDATE users 
            SET password_hash=:password
            WHERE email=:email
""")
            await db.execute(query, {
                "password":encrypted_password,
                "email":request.email
            })
            await db.commit()
        return {
            "access_token":access_token,
            "user_email":request.email
        }

    
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"{e}"
        )
    finally:
        await db.close()


async def register(request: Login_request):
    db = SessionLocal()
    encrypted_password = encrypt_password(password=request.password)
    payload = Payload(
        email=request.email
    )
    access_token = create_access_token(data=payload)
    try:
        query = text("""INSERT INTO users(email, password_hash) VALUES(:email ,:encrypted_password)""")
        await db.execute(query,{
            "email":request.email,
            "encrypted_password":encrypted_password
        })
        await db.commit()
        return {
            "access_token":access_token,
            "user_email":request.email
        }

    except Exception as e:
        await db.rollback()
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