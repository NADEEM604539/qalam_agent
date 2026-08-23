import os
import tempfile

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

load_dotenv()


DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "4000")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

TIDB_CA_CERT = os.getenv("TIDB_CA_CERT")


if not TIDB_CA_CERT:
    raise RuntimeError(
        "TIDB_CA_CERT environment variable is not configured."
    )


# Convert escaped \n characters back into real newlines
TIDB_CA_CERT = TIDB_CA_CERT.replace("\\n", "\n")


# Create a temporary certificate file
ca_file = tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".pem",
    delete=False,
)

ca_file.write(TIDB_CA_CERT)
ca_file.flush()
ca_file.close()


DATABASE_URL = (
    f"mysql+asyncmy://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/"
    f"{DB_NAME}"
)


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    DATABASE_URL,
    connect_args={
        "ssl_ca": ca_file.name,
    },
    pool_pre_ping=True,
    pool_recycle=1800,
)


SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)