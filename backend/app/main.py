from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.projects import router as projects_router
from app.api.workspaces import router as workspaces_router
from app.core.database import Base, engine
from app.core.storage import ensure_directories

app = FastAPI(
    title="AI Debugging Assistant API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"},
    )


app.include_router(auth_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(workspaces_router, prefix="/api")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    ensure_directories()
