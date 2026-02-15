import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.config.settings import settings
from app.config.database import engine, Base
from app.routes.auth import router as auth_router
from app.routes.jobs import router as jobs_router
from app.routes.matching import router as matching_router
from app.routes.saved_jobs import router as saved_jobs_router

logger = logging.getLogger(__name__)
app = FastAPI(title="Jobzie API")


@app.on_event("startup")
async def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified.")
    except OperationalError as e:
        logger.warning(
            "Could not connect to the database at startup. "
            "Start PostgreSQL (e.g. brew services start postgresql) or check DATABASE_URL. "
            "API will start but DB-dependent routes will fail until the DB is available. Error: %s",
            e,
        )
    from app.services.match_job_queue import start_match_worker
    app.state.match_worker_task = start_match_worker()


@app.on_event("shutdown")
async def on_shutdown():
    if getattr(app.state, "match_worker_task", None):
        app.state.match_worker_task.cancel()
        try:
            await app.state.match_worker_task
        except Exception:
            pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(matching_router)
app.include_router(saved_jobs_router)
