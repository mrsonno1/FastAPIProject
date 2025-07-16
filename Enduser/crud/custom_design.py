from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from db import models
from typing import Optional, Dict, Any
import math
import base64
import io
from PIL import Image
from services.storage_service import storage_service
from fastapi import UploadFile


def get_images_paginated(
        db: Session,
        page: int = 1,
        size: int = 10,
        category: Optional[str] = None,
        display_name: Optional[str] = None,
        orderBy: Optional[str] = None
) -> Dict[str, Any]:
    """이미지 목록을 페이지네이션하여 조회"""

    query = db.query(models.Image)

    # 필터링
    if category:
        query = query.filter(models.Image.category == category)
    if display_name:
        query = query.filter(models.Image.display_name.contains(display_name))

    # 정렬
    if orderBy:
        if orderBy.lower().endswith(' desc'):
            column = orderBy.replace(' desc', '').strip()
            if hasattr(models.Image, column):
                query = query.order_by(getattr(models.Image, column).desc())
        elif orderBy.lower().endswith(' asc'):
            column = orderBy.replace(' asc', '').strip()
            if hasattr(models.Image, column):
                query = query.order_by(getattr(models.Image, column).asc())
    else:
        query = query.order_by(models.Image.uploaded_at.desc())

    # 전체 카운트
    total_count = query.count()

    # 페이지네이션
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {
        "total_count": total_count,
        "items": items
    }


def get_colors_paginated(
        db: Session,
        page: int = 1,
        size: int = 10,
        color_name: Optional[str] = None,
        orderBy: Optional[str] = None
) -> Dict[str, Any]:
    """색상 목록을 페이지네이션하여 조회"""

    query = db.query(models.Color)

    # 필터링
    if color_name:
        query = query.filter(models.Color.color_name.contains(color_name))

    # 정렬
    if orderBy:
        if orderBy.lower().endswith(' desc'):
            column = orderBy.replace(' desc', '').strip()
            if hasattr(models.Color, column):
                query = query.order_by(getattr(models.Color, column).desc())
        elif orderBy.lower().endswith(' asc'):
            column = orderBy.replace(' asc', '').strip()
            if hasattr(models.Color, column):
                query = query.order_by(getattr(models.Color, column).asc())
    else:
        query = query.order_by(models.Color.updated_at.desc())

    # 전체 카운트
    total_count = query.count()

    # 페이지네이션
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {
        "total_count": total_count,
        "items": items
    }


def get_custom_design_detail(db: Session, design_id: int, user_id: str) -> Optional[Dict[str, Any]]:
    """커스텀 디자인 상세 정보 조회"""

    design = db.query(models.CustomDesign).filter(
        models.CustomDesign.id == design_id,
        models.CustomDesign.user_id == user_id
    ).first()

    if not design:
        return None

    # 각 컴포넌트 정보 조회
    def get_component_info(image_id: str, color_id: str, transparency: str):
        if not image_id or not color_id:
            return None

        image = db.query(models.Image).filter(models.Image.id == image_id).first()
        color = db.query(models.Color).filter(models.Color.id == color_id).first()

        if not image or not color:
            return None

        return {
            "image_id": image_id,
            "image_url": image.public_url,
            "image_name": image.display_name,
            "RGB_id": color_id,
            "RGB_color": color.color_values,
            "RGB_name": color.color_name,
            "size": 100,
            "opacity": int(transparency) if transparency else 100
        }

    return {
        "item_name": design.item_name,
        "design_line": get_component_info(
            design.design_line_image_id,
            design.design_line_color_id,
            design.line_transparency
        ),
        "design_base1": get_component_info(
            design.design_base1_image_id,
            design.design_base1_color_id,
            design.base1_transparency
        ),
        "design_base2": get_component_info(
            design.design_base2_image_id,
            design.design_base2_color_id,
            design.base2_transparency
        ),
        "design_pupil": get_component_info(
            design.design_pupil_image_id,
            design.design_pupil_color_id,
            design.pupil_transparency
        ),
        "graphic_diameter": design.graphic_diameter,
        "optic_zone": design.optic_zone
    }


def create_custom_design(db: Session, design_data: Dict[str, Any], user_id: str) -> models.CustomDesign:
    """커스텀 디자인 생성 - Manager 버전과 동일한 구조"""

    # 이미지 데이터 처리 (Base64를 UploadFile로 변환하여 S3에 업로드)
    image_data = design_data.get("image_data")
    main_image_url = None

    if image_data:
        try:
            # Base64에서 헤더 제거 (data:image/png;base64, 등)
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            # Base64 디코딩
            image_bytes = base64.b64decode(image_data)

            # PIL로 이미지 검증 및 처리
            image = Image.open(io.BytesIO(image_bytes))

            # PNG 형식으로 변환
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_buffer.seek(0)

            # UploadFile 객체 생성
            class FakeUploadFile:
                def __init__(self, content, filename, content_type):
                    self.file = io.BytesIO(content)
                    self.filename = filename
                    self.content_type = content_type

                def read(self, size=-1):
                    return self.file.read(size)

            fake_file = FakeUploadFile(
                img_buffer.getvalue(),
                f"{design_data['item_name']}.png",
                "image/png"
            )

            # S3에 업로드
            upload_result = storage_service.upload_file(fake_file)

            if upload_result:
                main_image_url = upload_result["public_url"]

        except Exception as e:
            print(f"이미지 업로드 실패: {e}")
            pass  # 이미지 업로드 실패 시 None으로 유지

    # 커스텀 디자인 생성 - Manager와 동일한 구조
    db_design = models.CustomDesign(
        user_id=user_id,
        item_name=design_data["item_name"],
        main_image_url=main_image_url,
        design_line_image_id=design_data.get("design_line", {}).get("image_id"),
        design_line_color_id=design_data.get("design_line", {}).get("RGB_id"),
        design_base1_image_id=design_data.get("design_base1", {}).get("image_id"),
        design_base1_color_id=design_data.get("design_base1", {}).get("RGB_id"),
        design_base2_image_id=design_data.get("design_base2", {}).get("image_id"),
        design_base2_color_id=design_data.get("design_base2", {}).get("RGB_id"),
        design_pupil_image_id=design_data.get("design_pupil", {}).get("image_id"),
        design_pupil_color_id=design_data.get("design_pupil", {}).get("RGB_id"),
        line_transparency=str(design_data.get("design_line", {}).get("opacity", 100)),
        base1_transparency=str(design_data.get("design_base1", {}).get("opacity", 100)),
        base2_transparency=str(design_data.get("design_base2", {}).get("opacity", 100)),
        pupil_transparency=str(design_data.get("design_pupil", {}).get("opacity", 100)),
        graphic_diameter=design_data.get("graphic_diameter"),
        optic_zone=design_data.get("optic_zone"),
        status="1"  # 완료 상태로 설정
    )

    db.add(db_design)
    db.commit()
    db.refresh(db_design)

    return db_design


def get_user_custom_designs_paginated(
        db: Session,
        user_id: str,
        page: int = 1,
        size: int = 10,
        orderBy: Optional[str] = None
) -> Dict[str, Any]:
    """사용자의 커스텀 디자인 목록을 페이지네이션하여 조회 - Manager 버전과 동일한 구조"""

    query = db.query(models.CustomDesign).filter(
        models.CustomDesign.user_id == user_id,
        models.CustomDesign.status == "1"  # 완료된 디자인만 조회
    )

    # 정렬
    if orderBy:
        if orderBy.lower().endswith(' desc'):
            column = orderBy.replace(' desc', '').strip()
            if hasattr(models.CustomDesign, column):
                query = query.order_by(getattr(models.CustomDesign, column).desc())
        elif orderBy.lower().endswith(' asc'):
            column = orderBy.replace(' asc', '').strip()
            if hasattr(models.CustomDesign, column):
                query = query.order_by(getattr(models.CustomDesign, column).asc())
    else:
        query = query.order_by(models.CustomDesign.created_at.desc())

    # 전체 카운트
    total_count = query.count()

    # 페이지네이션
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {
        "total_count": total_count,
        "items": items
    }


def get_design_by_id(db: Session, design_id: int, user_id: str) -> Optional[models.CustomDesign]:
    """ID로 커스텀 디자인 조회 (사용자 본인의 디자인만)"""
    return db.query(models.CustomDesign).filter(
        models.CustomDesign.id == design_id,
        models.CustomDesign.user_id == user_id
    ).first()