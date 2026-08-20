import asyncio
import sys

from fastapi import APIRouter, FastAPI, HTTPException
from backend.routers.login import router as login_router
from sqlalchemy import text
from backend.database.database import SessionLocal
import uvicorn
from uvicorn import Config, Server

app = FastAPI(title="Backend of Automate Qalam")
router = APIRouter()

# ... your routes ...

app.include_router(router=login_router, prefix="/api")


# class ProactorServer(Server):
#     """Forces ProactorEventLoop on Windows so Playwright's subprocess calls work."""

#     def run(self, sockets=None):
#         loop = asyncio.ProactorEventLoop()
#         asyncio.set_event_loop(loop)
#         loop.run_until_complete(self.serve(sockets=sockets))


if __name__ == "__main__":
    config = Config(
        app="backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

    # if sys.platform == "win32":
    #     ProactorServer(config=config).run()
    # else:
    #     uvicorn.run(config.app, host=config.host, port=config.port, reload=config.reload)