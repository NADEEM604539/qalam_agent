from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

from dotenv import load_dotenv

import os
import ssl


load_dotenv()


# ============================================================
# DATABASE CONFIG
# ============================================================

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "4000")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

TIDB_CA_CERT = os.getenv("TIDB_CA_CERT")


if not DB_HOST:
    raise RuntimeError("DB_HOST is not configured")

if not DB_USER:
    raise RuntimeError("DB_USER is not configured")

if not DB_PASSWORD:
    raise RuntimeError("DB_PASSWORD is not configured")

if not DB_NAME:
    raise RuntimeError("DB_NAME is not configured")

if not TIDB_CA_CERT:
    raise RuntimeError("TIDB_CA_CERT is not configured")


# ============================================================
# SSL / TLS
# ============================================================

ssl_context = ssl.create_default_context()

ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED

ssl_context.load_verify_locations(
    cadata=TIDB_CA_CERT
)


# ============================================================
# DATABASE URL
# ============================================================

DATABASE_URL = (
    f"mysql+asyncmy://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


# ============================================================
# SQLALCHEMY
# ============================================================

class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    DATABASE_URL,

    connect_args={
        "ssl": ssl_context
    },

    pool_pre_ping=True,
    pool_recycle=1800,

    # Vercel/serverless environments benefit from a small pool.
    pool_size=2,
    max_overflow=3,
)


SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)