from fastapi import APIRouter, FastAPI, HTTPException
from backend.routers.login import router as login_router
from sqlalchemy import text
from backend.database.database import SessionLocal

app = FastAPI(
    title="Backend of Automate Qalam"
)
router = APIRouter()

@router.get("/health")
async def health():
    try:
        db = SessionLocal()
        query = text("""SELECT 2+2 AS RESULT""")

        results = db.execute(query,{})
        return {"status": "ok", "result": results.fetchone()[0]}
    except:
         raise HTTPException(
                status_code=500,
                detail="CONNECTION TO DATABASE FAILED"
            )
    finally:
        if db:
            db.close()



app.include_router(router=login_router, prefix="/api")


def main() -> None:
    print("Hello from backend!")
