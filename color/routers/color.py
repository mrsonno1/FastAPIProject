# routers/color.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import math
from db.database import get_db
from color.schemas import color as color_schema
from color.crud import color as color_crud
from color.schemas.color import PaginatedColorResponse
from typing import Optional
from portfolio.schemas import portfolio as portfolio_schema

router = APIRouter(prefix="/colors", tags=["Colors"])

@router.get("/list", response_model=PaginatedColorResponse)
def list_all_colors(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        orderBy: Optional[str] = Query(None, description="정렬 기준 (예: 'color_name asc')"),
        searchText: Optional[str] = Query(None, description="통합 검색어"),
        db: Session = Depends(get_db)
):
    """
    모든 컬러 목록을 페이지네이션하여 조회합니다.
    """
    paginated_data = color_crud.get_colors_paginated(
        db, page=page, size=size,
        orderBy=orderBy, searchText=searchText  # <-- CRUD 함수에 전달
    )

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


@router.delete("/{color_id}", response_model=portfolio_schema.StatusResponse, status_code=status.HTTP_200_OK)
def delete_single_color(
    color_id: int,
    db: Session = Depends(get_db)
    # 필요 시, 인증/권한 검사 추가
    # current_user: models.AdminUser = Depends(get_current_user)
):
    """
    ID로 특정 컬러 데이터를 삭제합니다.
    """
    try:
        was_deleted = color_crud.delete_color_by_id(db, color_id=color_id)
        if not was_deleted:
            raise HTTPException(status_code=404, detail="해당 ID의 컬러를 찾을 수 없습니다.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

    return portfolio_schema.StatusResponse(status="success", message="컬러가 성공적으로 삭제되었습니다.")


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
    """
    db_color = color_crud.get_color_by_name(db, color_name=name)
    if db_color is None:
        raise HTTPException(status_code=404, detail="해당 이름의 컬러를 찾을 수 없습니다.")
    return db_color


@router.put("/fix/{color_id}", response_model=color_schema.ColorResponse)
def fix_color_by_id(
    # 경로 변수로 숫자 ID를 받습니다.
    color_id: int,
    # 요청 본문은 그대로 Pydantic 스키마를 사용합니다.
    color_update: color_schema.ColorUpdate,
    db: Session = Depends(get_db)
):
    """
    ID로 특정 컬러를 찾아, 이름과 값을 수정합니다.
    """
    # 1. ID로 수정할 컬러 조회
    db_color = color_crud.get_color_by_id(db, color_id=color_id)
    if db_color is None:
        raise HTTPException(status_code=404, detail="수정할 컬러를 찾을 수 없습니다.")

    # 2. (선택사항) 컬러 이름은 Pydantic 스키마에 없지만, 만약 함께 수정한다면
    #    아래와 같이 중복 검사 로직을 추가할 수 있습니다.
    #    (현재 ColorUpdate 스키마에는 color_name이 없으므로 이 부분은 참고용입니다.)
    # if color_update.color_name:
    #     existing_color = color_crud.get_color_by_name(db, color_name=color_update.color_name)
    #     if existing_color and existing_color.id != color_id:
    #         raise HTTPException(status_code=409, detail="이미 사용 중인 컬러 이름입니다.")

    # 3. CRUD 함수를 호출하여 업데이트
    return color_crud.update_color(db=db, db_color=db_color, color_update=color_update)