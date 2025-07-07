from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import math
from portfolio.schemas import portfolio as portfolio_schema
from db import models
from db.database import get_db
from portfolio.crud import portfolio as portfolio_CRUD
from services.storage_service import storage_service
from core.security import get_current_user # 인증 의존성 임포트

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.post("/", response_model=portfolio_schema.PortfolioApiResponse,
             status_code=status.HTTP_200_OK
)
def create_new_portfolio(
    portfolio_str: str = Form(..., alias="portfolio"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):
    """
     "exposed_countries":  {
        "대한민국": true,
        "미국": true,
        "중국": true,
        "호주": true,
        "캐나다": true,
        "인도": true,
        "베트남": true,
        "러시아": true
      },
    """

    try:
        portfolio_dict = json.loads(portfolio_str)
        portfolio_data = portfolio_schema.PortfolioCreate(**portfolio_dict)

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="전송된 'portfolio' 데이터의 JSON 형식이 잘못되었습니다.")
    except Exception as e:  # Pydantic 유효성 검사 실패 시
        raise HTTPException(status_code=422, detail=f"데이터 유효성 검사 실패: {e}")

    if portfolio_CRUD.get_portfolio_by_design_name(db, design_name=portfolio_data.design_name):
        raise HTTPException(status_code=409, detail="이미 사용 중인 디자인명입니다.")

    #이미지 업로드
    upload_result = storage_service.upload_file(file)
    if not upload_result:
        raise HTTPException(status_code=500, detail="메인 이미지 업로드에 실패했습니다.")

    #이미지 업로드 url적용
    portfolio_data.main_image_url = upload_result["public_url"]

    #데이터 베이스 적용
    created_portfolio = portfolio_CRUD.create_portfolio(
        db=db,
        portfolio=portfolio_data,
        user_id=current_user.id
    )

    #리스폰 모델로 변환
    response_data = portfolio_schema.PortfolioResponse.model_validate(created_portfolio)


    #반환값 생성
    return portfolio_schema.PortfolioApiResponse(
        success=True,
        message="포트폴리오가 성공적으로 생성되었습니다.",
        data=response_data
    )

@router.get("/list", response_model=portfolio_schema.PaginatedPortfolioResponse)
def list_all_portfolios(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        design_name: Optional[str] = Query(None, description="디자인명으로 검색"),
        color_name: Optional[str] = Query(None, description="컬러명으로 검색"),
        exposed_countries: Optional[List[str]] = Query(None, description="노출 국가로 검색"),
        is_fixed_axis: Optional[bool] = Query(None, description="고정 축 여부로 검색"),
        db: Session = Depends(get_db)
):
    """
    모든 포트폴리오 목록을 검색 조건과 함께 페이지네이션하여 조회합니다.
    """
    paginated_data = portfolio_CRUD.get_portfolios_paginated(
        db,
        page=page,
        size=size,
        design_name=design_name,
        color_name=color_name,
        exposed_countries=exposed_countries,
        is_fixed_axis=is_fixed_axis
    )

    items = paginated_data["items"]
    total_count = paginated_data["total_count"]

    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    return {
        "total_count": total_count,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": items,
    }

@router.get("/{design_name}", response_model=portfolio_schema.PortfolioResponse)
def read_single_portfolio(
        design_name: str,
        db: Session = Depends(get_db)
):
    db_portfolio = portfolio_CRUD.get_portfolio_by_design_name(db, design_name=design_name)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
    return db_portfolio

