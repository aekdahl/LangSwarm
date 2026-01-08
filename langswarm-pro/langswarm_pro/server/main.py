from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production this should be stricter
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routers import governance, scheduler, memory

app.include_router(governance.router, prefix=f"{settings.API_V1_STR}/governance", tags=["governance"])
app.include_router(scheduler.router, prefix=f"{settings.API_V1_STR}/scheduler", tags=["scheduler"])
app.include_router(memory.router, prefix=f"{settings.API_V1_STR}/memory", tags=["memory"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
