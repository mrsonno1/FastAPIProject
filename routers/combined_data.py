from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from db.database import get_db
from schemas.combined_data import CombinedDataResponse

from portfolio.crud import portfolio as portfolio_crud
from custom_design.crud import custom_design as custom_design_crud

router = APIRouter(prefix="/combined-data", tags=["Combined Data"])

@router.get("/", response_model=CombinedDataResponse)
def get_all_combined_data(
    db: Session = Depends(get_db),
    portfolio_page: int = Query(1, ge=1),
    portfolio_size: int = Query(100, ge=1, le=1000),
    custom_design_page: int = Query(1, ge=1),
    custom_design_size: int = Query(100, ge=1, le=1000),
):
    """
    모든 포트폴리오, 커스텀 디자인 목록을 한 번에 조회합니다.
    각 섹션별로 페이지네이션을 적용할 수 있습니다.
    """
    portfolios_data = portfolio_crud.get_portfolios_paginated(
        db, page=portfolio_page, size=portfolio_size
    )
    custom_designs_data = custom_design_crud.get_designs_paginated(
        db, page=custom_design_page, size=custom_design_size
    )

    return CombinedDataResponse(
        portfolios=portfolios_data["items"],
        custom_designs=custom_designs_data["items"],
    )
