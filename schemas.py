# emotional_budget_tracker/schemas.py
from pydantic import BaseModel
from typing import Optional

class TransactionCreate(BaseModel):
    amount: float
    type: str
    category: str
    date: str
    source: str
    description: Optional[str] = "No description"
    tags: Optional[str] = ""
    due_date: Optional[str] = None
    emotional_weight: Optional[str] = "medium"
    mode: Optional[str] = "structured"

class TransactionOut(BaseModel):
    message: str
    transaction_id: str

class BalanceUpdate(BaseModel):
    user_id: str
    balance: float
    last_updated: Optional[str] = None

class BalanceOut(BaseModel):
    message: str
    balance_id: str

# emotional_budget_tracker/schemas.py
from pydantic import BaseModel
from typing import Optional

# --- Emotion Tags ---
class EmotionTagCreate(BaseModel):
    tag: str
    intensity: Optional[str] = "medium"

class EmotionTagOut(BaseModel):
    message: str
    tag_id: str

# --- Prompts ---
class EmotionPromptOut(BaseModel):
    prompt: str

class TimePromptOut(BaseModel):
    prompt: str

# --- Interest ---
class InterestUpdate(BaseModel):
    interest: str
    level: Optional[str] = "medium"

class InterestOut(BaseModel):
    message: str
    interest_id: str

# --- Inspiration ---
class InspirationQuoteOut(BaseModel):
    quote: str

# --- Rituals ---
class RitualSetup(BaseModel):
    name: str
    description: Optional[str] = None
    date: Optional[str] = None

class RitualOut(BaseModel):
    message: str
    ritual_id: str

# --- Users ---
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserOut(BaseModel):
    id: str
    username: str
    email: str

# --- Valhalla Tags ---
class ValhallaTagCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ValhallaTagOut(BaseModel):
    message: str
    tag_id: str

# --- Ritual Setup Items ---
from typing import List

class Component(BaseModel):
    name: str
    amount: float
    description: Optional[str] = None

class SetupItemCreate(BaseModel):
    user_id: str
    name: str
    category: str
    amount: float
    frequency: str
    due_date: str
    archetype: str
    symbolic_tag: str
    components: Optional[List[Component]] = []
    principal: Optional[float] = 0.0
    interest_rate: Optional[float] = 0.0
    recurrence: Optional[str] = "none"
    arc_enabled: Optional[bool] = False
    emotion_tag_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    symbolic_time: Optional[str] = None

class SetupItemOut(BaseModel):
    setup_id: str
    user_id: str
    name: str
    category: str
    amount: float
    frequency: str
    recurrence: str
    is_one_time: bool
    principal: float
    interest_rate: float
    includes_interest: bool
    due_date: str
    emotion_tag_id: Optional[str]
    archetype: str
    symbolic_tag: str
    arc_enabled: bool
    symbolic_time: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    active: bool
    components: List[Component]
    monthly_equivalent: Optional[float] = None
    total_components: Optional[float] = None
