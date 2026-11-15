import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import overview, projects, map as map_router, insights, quality, meta

app = FastAPI(
    title="Ontario Infrastructure Decision Intelligence API",
    description="Read-only analytical API over the Ontario Builds: Communities dataset.",
    version="1.0.0",
)

cors_origins = os.environ.get("API_CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(overview.router)
app.include_router(projects.router)
app.include_router(map_router.router)
app.include_router(insights.router)
app.include_router(quality.router)
app.include_router(meta.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
