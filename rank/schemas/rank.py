# rank/schemas/rank.py
from pydantic import BaseModel
from typing import List, Optional

class RankItem(BaseModel):
    image: Optional[str] = None
    name: str
    view: int

    class Config:
        orm_mode = True

class CustomDesignStatus(BaseModel):
    wait: int
    reject: int
    under_review: int
    complet: int
    total: int

class ProgressStatus(BaseModel):
    wait: int
    pregress: int
    delay: int
    delivery_completed: int
    total: int

class RankResponse(BaseModel):
    released_product: List[RankItem]
    portfolio: List[RankItem]
    custom_design: CustomDesignStatus
    progress_status: ProgressStatus
