from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from db.database import get_db
from db import models
from core.security import get_current_user
from Enduser.schemas import portfolio as portfolio_schema
from Enduser.crud import portfolio as portfolio_crud
import math

router = APIRouter(tags=["Portfolio"])


@router.get("/portfolio/list", response_model=portfolio_schema.PaginatedPortfolioResponse)
def get_portfolio_list(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        exposed_countries: Optional[List[str]] = Query(None, description="노출 국가 ID 필터링"),
        is_fixed_axis: Optional[str] = Query(None, description="축고정 여부 필터링 (Y/N)"),
        item_name: Optional[str] = Query(None, description="디자인 이름으로 검색"),
        orderBy: Optional[str] = Query("popularity", description="정렬 기준 (popularity: 인기순-기본값, latest: 최신순)"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """
    포트폴리오 목록 조회

    - exposed_countries: 노출 국가 ID 목록으로 필터링
    - is_fixed_axis: 축고정 여부로 필터링 (Y 또는 N)
    - item_name: 디자인 이름으로 검색
    - orderBy: 정렬 기준
      - popularity: 인기순 (기본값) - 조회수 기준, 동일한 경우 디자인명 ABC순
      - latest: 최신순 - 생성일 기준
    """

    # is_fixed_axis 검증
    if is_fixed_axis and is_fixed_axis not in ['Y', 'N']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="is_fixed_axis는 'Y' 또는 'N'이어야 합니다."
        )

    # orderBy 검증
    if orderBy not in ['popularity', 'latest']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="orderBy는 'popularity' 또는 'latest'여야 합니다."
        )

    paginated_data = portfolio_crud.get_portfolios_paginated(
        db=db,
        page=page,
        size=size,
        exposed_countries=exposed_countries,
        is_fixed_axis=is_fixed_axis,
        item_name=item_name,
        orderBy=orderBy
    )

    total_count = paginated_data["total_count"]
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    return portfolio_schema.PaginatedPortfolioResponse(
        total_count=total_count,
        total_pages=total_pages,
        page=page,
        size=size,
        items=paginated_data["items"]
    )


@router.get("/portfolio/{item_name}", response_model=portfolio_schema.PortfolioDetailResponse)
def get_portfolio_detail(
        item_name: str,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """
    포트폴리오 디자인 항목 조회

    디자인 이름으로 포트폴리오의 상세 정보를 조회합니다.
    조회시 조회수가 증가합니다.
    """

    portfolio_detail = portfolio_crud.get_portfolio_detail(
        db=db,
        item_name=item_name
    )

    if not portfolio_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="포트폴리오를 찾을 수 없습니다."
        )

    return portfolio_schema.PortfolioDetailResponse(**portfolio_detail)