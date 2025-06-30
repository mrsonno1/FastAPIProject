from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from schemas import custom_design as custom_design_schema
from db import models

router = APIRouter(prefix="/custom-designs", tags=["Custom Designs"])


def create_design(db: Session, design: custom_design_schema.CustomDesignCreate):
    design_data = design.model_dump()
    db_design = models.CustomDesign(**design_data)
    db.add(db_design)
    db.commit()
    db.refresh(db_design)
    return db_design

def get_design_by_id(db: Session, design_id: int):
    return db.query(models.CustomDesign).filter(models.CustomDesign.id == design_id).first()

def get_all_designs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CustomDesign).order_by(models.CustomDesign.id.desc()).offset(skip).limit(limit).all()

def update_design_status(db: Session, design_id: int, status_update: custom_design_schema.CustomDesignStatusUpdate):
    db_design = get_design_by_id(db, design_id)
    if db_design:
        db_design.status = status_update.status
        db.commit()
        db.refresh(db_design)
    return db_design

# --- API 엔드포인트 ---

@router.post("/", response_model=custom_design_schema.CustomDesignResponse, status_code=status.HTTP_201_CREATED)
def create_new_custom_design(
    design: custom_design_schema.CustomDesignCreate,
    db: Session = Depends(get_db)
):
    """새로운 커스텀 디자인 요청을 생성합니다."""
    # 코드명 중복 검사
    if db.query(models.CustomDesign).filter(models.CustomDesign.code_name == design.code_name).first():
        raise HTTPException(status_code=409, detail="이미 사용 중인 코드명입니다.")
    return create_design(db=db, design=design)

@router.get("/", response_model=List[custom_design_schema.CustomDesignResponse])
def read_all_custom_designs(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """모든 커스텀 디자인 목록을 조회합니다."""
    designs = get_all_designs(db, skip=skip, limit=limit)
    return designs

@router.get("/{design_id}", response_model=custom_design_schema.CustomDesignResponse)
def read_single_custom_design(design_id: int, db: Session = Depends(get_db)):
    """ID로 특정 커스텀 디자인의 상세 정보를 조회합니다."""
    db_design = get_design_by_id(db, design_id)
    if db_design is None:
        raise HTTPException(status_code=404, detail="디자인을 찾을 수 없습니다.")
    return db_design

@router.patch("/status/{design_id}", response_model=custom_design_schema.CustomDesignResponse)
def update_status_of_design(
    design_id: int,
    status_update: custom_design_schema.CustomDesignStatusUpdate,
    db: Session = Depends(get_db)
):
    """특정 커스텀 디자인의 '상태'만 수정합니다."""
    updated_design = update_design_status(db, design_id, status_update)
    if updated_design is None:
        raise HTTPException(status_code=404, detail="디자인을 찾을 수 없습니다.")
    return updated_design