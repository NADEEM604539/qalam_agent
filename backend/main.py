import asyncio
import sys
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from backend.routers.login import router as login_router
from backend.routers.dashboard import router as dashboard_router

from sqlalchemy import text
from backend.database.database import SessionLocal
from backend.services.scheduler import (
    start_scheduler,
    stop_scheduler,
    get_job_status,
)
from uvicorn import Config, Server


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: start the background scheduler that runs
    # marks_change_workflow() every 1 minute.
    start_scheduler()
    yield
    # Shutdown: stop the scheduler cleanly.
    stop_scheduler()


app = FastAPI(title="Backend of Automate Qalam", lifespan=lifespan)

origins = [
    "http://localhost:3000",       # Local React development
    "http://127.0.0.1:5173",      # Local Vite development
    "https://myproductionapp.com"  # Production domain
]

# 2. Add CORSMiddleware to your application stack
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # Allowed origins
    allow_credentials=True,          # Support cookies and auth headers
    allow_methods=["*"],             # Allowed HTTP methods (GET, POST, etc.)
    allow_headers=["*"],             # Allowed request headers
)

# ... your routes ...

app.include_router(router=login_router, prefix="/api")
app.include_router(router=dashboard_router, prefix="/api")


# class ProactorServer(Server):
#     """Forces ProactorEventLoop on Windows so Playwright's subprocess calls work."""

#     def run(self, sockets=None):
#         loop = asyncio.ProactorEventLoop()
#         asyncio.set_event_loop(loop)
#         loop.run_until_complete(self.serve(sockets=sockets))

@app.get('/health')
async def testing():
    # Lightweight health check ONLY — does NOT trigger the workflow.
    # The workflow now runs on its own background schedule (every 1
    # minute), started at app startup. Running it inline here meant
    # every health-check hit (e.g. from an uptime monitor) fired a
    # full scrape/email run, which is not what a health check should do.
    return {
        "status": "successful"
    }


@app.get('/scheduler/status')
async def scheduler_status():
    # Lets you confirm the scheduler is alive and see when it last/next runs.
    return get_job_status()


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
