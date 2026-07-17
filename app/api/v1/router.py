from fastapi import APIRouter

from app.api.v1.salud import router as salud_router

router = APIRouter()
router.include_router(salud_router, tags=["salud"])
