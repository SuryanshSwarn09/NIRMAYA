from fastapi import APIRouter
from app.api.v1.endpoints import health, meta, patients

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["Health & Telemetry"])
api_router.include_router(meta.router, prefix="", tags=["Interoperability & Metadata"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patient Vault"])
