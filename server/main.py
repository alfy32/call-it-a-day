from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from database import engine, Base, SessionLocal
from models import Settings
from routers import sync, summary, sessions, manual, settings

_STATIC_DIR = Path(__file__).parent / "static"

_SETTING_DEFAULTS = {
    "weekly_target_hours": "40",
    "daily_target_hours": "8",
    "tracking_start_date": str(date.today()),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for key, value in _SETTING_DEFAULTS.items():
            if not db.query(Settings).filter(Settings.key == key).first():
                db.add(Settings(key=key, value=value))
        db.commit()
    finally:
        db.close()
    yield


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path == "/" or request.url.path.endswith((".html", ".js")):
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
        return response


app = FastAPI(title="Call It a Day", lifespan=lifespan)
app.add_middleware(NoCacheMiddleware)
app.include_router(sync.router)
app.include_router(summary.router)
app.include_router(sessions.router)
app.include_router(manual.router)
app.include_router(settings.router)
app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")
