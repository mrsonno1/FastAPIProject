from pydantic import BaseModel
from typing import List

from portfolio.schemas.portfolio import PortfolioResponse
from custom_design.schemas.custom_design import CustomDesignResponse

class CombinedDataResponse(BaseModel):
    portfolios: List[PortfolioResponse]
    custom_designs: List[CustomDesignResponse]
