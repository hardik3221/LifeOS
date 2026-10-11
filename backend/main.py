from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from backend.config import Settings
from backend.database import Base, build_engine
from backend.routes import tasks, goals, planner
from backend.services.planner import UnconfiguredPlanner

def create_app(settings: Settings | None = None, planner_service=None) -> FastAPI:
    settings = settings or Settings()
    engine = build_engine(settings.database_url)
    @asynccontextmanager
    async def lifespan(app):
        Base.metadata.create_all(engine)
        yield
        engine.dispose()
    app = FastAPI(title="LifeOS API", version="0.1.0", lifespan=lifespan)
    app.state.engine = engine
    app.state.planner = planner_service if planner_service is not None else UnconfiguredPlanner()
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "DELETE"],
                       allow_headers=["Content-Type", "Authorization"])
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.status_code, "message": exc.detail}}, headers=exc.headers)
    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        details = [{"field": ".".join(map(str, error["loc"])), "message": error["msg"], "type": error["type"]} for error in exc.errors()]
        return JSONResponse(status_code=422, content={"error": {"code": 422, "message": "Validation failed", "details": details}})
    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        return JSONResponse(status_code=503, content={"error": {"code": 503, "message": "Database unavailable"}})
    @app.get("/health", tags=["health"])
    def health():
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    app.include_router(tasks.router)
    app.include_router(goals.router)
    app.include_router(planner.router)
    return app

app = create_app()
