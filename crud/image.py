# crud/image.py
from sqlalchemy.orm import Session
from db import models


def get_image_by_display_name(db: Session, category: str, display_name: str):
    """category와 display_name의 조합으로 이미지 정보 조회"""
    return db.query(models.Image).filter(
        models.Image.category == category,
        models.Image.display_name == display_name
    ).first()


def update_image_file(db: Session, db_image: models.Image, new_object_name: str, new_public_url: str):
    """이미지 파일 교체 후 DB 정보(object_name, public_url) 업데이트"""
    db_image.object_name = new_object_name
    db_image.public_url = new_public_url
    db.commit()
    db.refresh(db_image)
    return db_image