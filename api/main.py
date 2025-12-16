# emotional_budget_tracker/api/main.py
from fastapi import APIRouter

# Create a unified router instead of a full app
router = APIRouter()

# Import sub-routers
from .tags_router import router as valhalla_tags_router

from .transactions_router import router as transactions_router
from .balances_router import router as balances_router
from .emotion_tags_router import router as emotion_tags_router
from .prompts_router import router as prompts_router
from .interest_router import router as interest_router
from .inspiration_router import router as inspiration_router
from .rituals_router import router as rituals_router
from .health_router import router as health_router

# Include them into the unified router
router.include_router(valhalla_tags_router)
router.include_router(health_router)

router.include_router(transactions_router)
router.include_router(balances_router)
router.include_router(emotion_tags_router)
router.include_router(prompts_router)
router.include_router(interest_router)
router.include_router(inspiration_router)
router.include_router(rituals_router)
