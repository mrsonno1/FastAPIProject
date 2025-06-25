# routers/color.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import math
from db.database import get_db
from schemas import color as color_schema
from crud import color as color_crud
from schemas.color import ColorResponse, PaginatedColorResponse

router = APIRouter(prefix="/colors", tags=["Colors"])

@router.get("/list", response_model=PaginatedColorResponse)
def list_all_colors(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        db: Session = Depends(get_db)
):
    """
    모든 컬러 목록을 페이지네이션하여 조회합니다.
    """
    paginated_data = color_crud.get_colors_paginated(db, page=page, size=size)

    total_count = paginated_data["total_count"]
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    return {
        "total_count": total_count,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": paginated_data["items"],
    }

@router.post("/", response_model=color_schema.ColorResponse, status_code=status.HTTP_201_CREATED)
def create_new_color(color: color_schema.ColorCreate, db: Session = Depends(get_db)):
    """
    새로운 컬러를 등록합니다. 이름이 중복되면 에러가 발생합니다.
    """
    db_color = color_crud.get_color_by_name(db, color_name=color.color_name)
    if db_color:
        raise HTTPException(status_code=409, detail="이미 사용 중인 컬러 이름입니다.")
    return color_crud.create_color(db=db, color=color)

@router.get("/check/{color_name}", response_model=color_schema.NameCheckResponse)
def check_color_name(color_name: str, db: Session = Depends(get_db)):
    """
    컬러 이름이 이미 존재하는지 확인합니다.
    """
    db_color = color_crud.get_color_by_name(db, color_name=color_name)
    return {"exists": db_color is not None}

@router.put("/", response_model=color_schema.ColorResponse)
def update_existing_color(
    # 요청 본문은 그대로 유지합니다.
    color_update: color_schema.ColorUpdate,
    # 경로 변수 대신 쿼리 파라미터로 받습니다.
    color_name: str = Query(..., description="수정할 컬러의 정확한 이름"),
    db: Session = Depends(get_db)
):
    """
    기존 컬러의 컬러 값과 흑백 타입을 수정합니다.
    (한글 이름 수정을 위해 쿼리 파라미터 사용)
    """
    db_color = color_crud.get_color_by_name(db, color_name=color_name)
    if db_color is None:
        raise HTTPException(status_code=404, detail="해당 이름의 컬러를 찾을 수 없습니다.")
    return color_crud.update_color(db=db, db_color=db_color, color_update=color_update)

@router.get("/search", response_model=color_schema.ColorResponse)
def search_single_color(
    # 경로 변수 대신 쿼리 파라미터로 받습니다.
    name: str = Query(..., description="검색할 컬러의 정확한 이름"),
    db: Session = Depends(get_db)
):
    """
    컬러 이름으로 특정 컬러의 상세 정보를 조회합니다.
    (한글 이름 검색을 위해 쿼리 파라미터 사용)
    """
    db_color = color_crud.get_color_by_name(db, color_name=name)
    if db_color is None:
        raise HTTPException(status_code=404, detail="해당 이름의 컬러를 찾을 수 없습니다.")
    return db_color