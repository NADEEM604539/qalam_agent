from fastapi import APIRouter, FastAPI, HTTPException
from backend.routers.login import router as login_router
from sqlalchemy import text
from backend.database.database import SessionLocal
import asyncio
import uvicorn
app = FastAPI(
    title="Backend of Automate Qalam"
)
router = APIRouter()

@app.get("/health")
async def health():
    try:
        db = SessionLocal()

        query = text("SELECT 2 + 2 AS result")

        result = await db.execute(query)

        return {
            "status": "ok",
            "result": result.scalar()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="CONNECTION TO DATABASE FAILED"
        )

    finally:
        await db.close()



app.include_router(router=login_router, prefix="/api")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(
        asyncio.WindowsProactorEventLoopPolicy()
    )
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )