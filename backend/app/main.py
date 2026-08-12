"""
App entrypoint. Run with:  uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import CORS_ORIGINS
from app.routers import complaints, copilot

# Create tables on startup if they don't exist yet. Fine for an
# assignment/demo project; for production you'd use Alembic migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AIVOA Complaint Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(complaints.router)
app.include_router(copilot.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
