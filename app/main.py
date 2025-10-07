from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.api.v1.routes import auth as auth_routes

app = FastAPI(title="Learning Platform API", version="1.0.0")


# origins = [
#     "http://localhost:5173"
# ]

# CORS
app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_origins=["*"],
    # allow_origins=[str(origin) for origin in settings.cors_allow_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}

# Versioned API
app.include_router(api_router, prefix=settings.api_v1_prefix)
