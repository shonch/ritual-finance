# valhalla/api/models.py
from pydantic import BaseModel

class ValhallaTagCreate(BaseModel):
    tag_name: str
    user_id: str
    description: str = "Testing Valhalla bridge to Phoenix"
    emoji: str = "🌀"
    category: str = "custom"
    archetype: str = "emergent"
    visibility: str = "private"

class TagResponse(BaseModel):
    tag_id: str
    status: str
