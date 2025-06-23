# routers/color.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from schemas import color as color_schema
from crud import color as color_crud

router = APIRouter(prefix="/colors", tags=["Colors"])

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

@router.put("/{color_name}", response_model=color_schema.ColorResponse)
def update_existing_color(
    color_name: str,
    color_update: color_schema.ColorUpdate,
    db: Session = Depends(get_db)
):
    """
    기존 컬러의 컬러 값을 수정합니다.
    """
    db_color = color_crud.get_color_by_name(db, color_name=color_name)
    if db_color is None:
        raise HTTPException(status_code=404, detail="해당 이름의 컬러를 찾을 수 없습니다.")
    return color_crud.update_color(db=db, db_color=db_color, color_update=color_update)



@router.get("/{color_name}", response_model=color_schema.ColorResponse)
def get_single_color(color_name: str, db: Session = Depends(get_db)):
    """
    컬러 이름으로 특정 컬러의 상세 정보를 조회합니다.
    """
    db_color = color_crud.get_color_by_name(db, color_name=color_name)
    if db_color is None:
        raise HTTPException(status_code=404, detail="해당 이름의 컬러를 찾을 수 없습니다.")
    return db_color
