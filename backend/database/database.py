from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase


load_dotenv()


# =========================
# Database Configuration
# =========================

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "4000")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


# =========================
# TiDB Cloud SSL Certificate
# =========================

BASE_DIR = Path(__file__).resolve().parents[3]

CA_CERT = BASE_DIR / "certs" / "ca.pem"

if not CA_CERT.exists():
    raise FileNotFoundError(
        f"TiDB Cloud CA certificate not found: {CA_CERT}"
    )


# =========================
# Database URL
# =========================

DATABASE_URL = (
    f"mysql+asyncmy://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/"
    f"{DB_NAME}"
)


# =========================
# SQLAlchemy Base
# =========================

class Base(DeclarativeBase):
    pass


# =========================
# Async Engine
# =========================

engine = create_async_engine(
    DATABASE_URL,
    connect_args={
        "ssl_ca": str(CA_CERT),
    },
    pool_pre_ping=True,
    pool_recycle=1800,
)


# =========================
# Async Session
# =========================

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)