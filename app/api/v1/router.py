"""
API v1 router aggregator
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, diagnosis, health, family

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(diagnosis.router, tags=["Diagnosis"])
# ✅ Family - بدون prefix لأن الـ endpoints في family.py عندها /family
api_router.include_router(family.router, tags=["Family"])