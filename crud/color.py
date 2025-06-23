# crud/color.py
from sqlalchemy.orm import Session
from db import models
from schemas import color as color_schema

def get_color_by_name(db: Session, color_name: str):
    """color_name으로 컬러 정보 조회"""
    return db.query(models.Color).filter(models.Color.color_name == color_name).first()

def create_color(db: Session, color: color_schema.ColorCreate):
    """새로운 컬러 생성"""
    db_color = models.Color(
        color_name=color.color_name,
        color_values=color.color_values,
        monochrome_type = color.monochrome_type
    )
    db.add(db_color)
    db.commit()
    db.refresh(db_color)
    return db_color

def update_color(db: Session, db_color: models.Color, color_update: color_schema.ColorUpdate):
    """컬러 값 업데이트"""
    db_color.color_values = color_update.color_values
    db_color.monochrome_type = color_update.monochrome_type
    db.commit()
    db.refresh(db_color)
    return db_color