import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from backend.DTO.login import Payload

load_dotenv()


SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_DAYS = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_DAYS", "15")
)

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set in .env")


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/login"
)


def create_access_token(
    data: Payload,
    expires_delta: timedelta | None = None,
) -> str:

    # Convert Pydantic model to dictionary
    to_encode = data.model_dump()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = (
            datetime.now(timezone.utc)
            + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        )

    to_encode["exp"] = expire

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> Payload:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:
        # Decode JWT
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        # Convert decoded dictionary back into Payload
        user_payload = Payload(**payload)

        return user_payload

    except InvalidTokenError:
        raise credentials_exception

    except Exception:
        raise credentials_exception
