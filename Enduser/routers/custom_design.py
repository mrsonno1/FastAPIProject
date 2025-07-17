from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from db import models
from core.security import get_current_user
from Enduser.schemas import custom_design as custom_design_schema
from Enduser.crud import custom_design as custom_design_crud
import math
from services.storage_service import storage_service  # 추가

router = APIRouter(tags=["Custom Design"])


@router.get("/images/list", response_model=custom_design_schema.PaginatedImageResponse)
def get_images_list(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        category: Optional[str] = Query(None, description="카테고리 필터링"),
        display_name: Optional[str] = Query(None, description="디자인 번호로 검색"),
        orderBy: Optional[str] = Query(None, description="정렬 기준"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """관리자가 등록한 라인/바탕1/바탕2/동공 디자인 목록 조회"""

    paginated_data = custom_design_crud.get_images_paginated(
        db=db,
        page=page,
        size=size,
        category=category,
        display_name=display_name,
        orderBy=orderBy
    )

    total_count = paginated_data["total_count"]
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    return custom_design_schema.PaginatedImageResponse(
        total_count=total_count,
        total_pages=total_pages,
        page=page,
        size=size,
        items=paginated_data["items"]
    )


@router.get("/colors/list", response_model=custom_design_schema.PaginatedColorResponse)
def get_colors_list(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        color_name: Optional[str] = Query(None, description="색상 번호로 검색"),
        orderBy: Optional[str] = Query(None, description="정렬 기준"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """관리자가 등록한 색상 목록 조회"""

    paginated_data = custom_design_crud.get_colors_paginated(
        db=db,
        page=page,
        size=size,
        color_name=color_name,
        orderBy=orderBy
    )

    total_count = paginated_data["total_count"]
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    return custom_design_schema.PaginatedColorResponse(
        total_count=total_count,
        total_pages=total_pages,
        page=page,
        size=size,
        items=paginated_data["items"]
    )


@router.get("/my-designs/list", response_model=custom_design_schema.PaginatedCustomDesignResponse)
def get_my_designs_list(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        orderBy: Optional[str] = Query(None, description="정렬 기준"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """커스텀디자인 완료 목록 조회"""

    paginated_data = custom_design_crud.get_user_custom_designs_paginated(
        db=db,
        user_id=current_user.username,
        page=page,
        size=size,
        orderBy=orderBy
    )

    total_count = paginated_data["total_count"]
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    # 응답 형식에 맞게 변환
    items = []
    for design in paginated_data["items"]:
        items.append(custom_design_schema.CustomDesignListItem(
            id=design.id,
            item_name=design.item_name,
            main_image_url=design.main_image_url or ""
        ))

    return custom_design_schema.PaginatedCustomDesignResponse(
        total_count=total_count,
        total_pages=total_pages,
        page=page,
        size=size,
        items=items
    )

@router.get("/my-designs/{design_id}", response_model=custom_design_schema.CustomDesignDetailResponse)
def get_my_design_detail(
        design_id: int,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """내 커스텀디자인 항목 조회"""

    design_detail = custom_design_crud.get_custom_design_detail(
        db=db,
        design_id=design_id,
        user_id=current_user.username
    )

    if not design_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="커스텀 디자인을 찾을 수 없습니다."
        )

    return custom_design_schema.CustomDesignDetailResponse(**design_detail)


@router.post("/my-designs", response_model=custom_design_schema.CustomDesignCreateResponse)
def create_my_design(
        # Form 데이터로 받기
        item_name: str = Form(..., description="디자인 이름"),
        color_name: str = Form(..., description="색상 이름"),
        design_line_image_id: Optional[str] = Form(None, description="라인 이미지 ID"),
        design_line_color_id: Optional[str] = Form(None, description="라인 색상 ID"),
        line_transparency: Optional[str] = Form("100", description="라인 투명도"),
        design_base1_image_id: Optional[str] = Form(None, description="바탕1 이미지 ID"),
        design_base1_color_id: Optional[str] = Form(None, description="바탕1 색상 ID"),
        base1_transparency: Optional[str] = Form("100", description="바탕1 투명도"),
        design_base2_image_id: Optional[str] = Form(None, description="바탕2 이미지 ID"),
        design_base2_color_id: Optional[str] = Form(None, description="바탕2 색상 ID"),
        base2_transparency: Optional[str] = Form("100", description="바탕2 투명도"),
        design_pupil_image_id: Optional[str] = Form(None, description="동공 이미지 ID"),
        design_pupil_color_id: Optional[str] = Form(None, description="동공 색상 ID"),
        pupil_transparency: Optional[str] = Form("100", description="동공 투명도"),
        graphic_diameter: Optional[str] = Form(None, description="그래픽 직경"),
        optic_zone: Optional[str] = Form(None, description="옵틱 존"),
        # 파일 업로드 - 파라미터 이름을 'file'로 수정
        file: Optional[UploadFile] = File(None, description="메인 이미지 파일"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """커스텀디자인 완료 목록 추가 - File 업로드 방식"""

    # 디자인명 중복 검사
    existing_design = db.query(models.CustomDesign).filter(
        models.CustomDesign.item_name == item_name,
        models.CustomDesign.user_id == current_user.username
    ).first()

    if existing_design:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 디자인명입니다."
        )

    # 파일 업로드 처리
    main_image_url = None
    if file:
        try:
            # 파일 검증
            if not file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="파일 이름이 없습니다."
                )

            # 파일 형식 확인 (선택사항)
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if file.content_type and file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(allowed_types)}"
                )

            print(f"업로드할 파일: {file.filename}, 타입: {file.content_type}")

            # 파일 업로드
            upload_result = storage_service.upload_file(file)
            if not upload_result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="이미지 업로드에 실패했습니다."
                )

            main_image_url = upload_result["public_url"]
            print(f"업로드 성공: {main_image_url}")

        except HTTPException:
            raise
        except Exception as e:
            print(f"이미지 업로드 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"이미지 업로드 중 오류가 발생했습니다: {str(e)}"
            )

    try:
        # Form 데이터 구성
        form_data = {
            "item_name": item_name,
            "color_name": color_name,
            "design_line_image_id": design_line_image_id,
            "design_line_color_id": design_line_color_id,
            "line_transparency": line_transparency,
            "design_base1_image_id": design_base1_image_id,
            "design_base1_color_id": design_base1_color_id,
            "base1_transparency": base1_transparency,
            "design_base2_image_id": design_base2_image_id,
            "design_base2_color_id": design_base2_color_id,
            "base2_transparency": base2_transparency,
            "design_pupil_image_id": design_pupil_image_id,
            "design_pupil_color_id": design_pupil_color_id,
            "pupil_transparency": pupil_transparency,
            "graphic_diameter": graphic_diameter,
            "optic_zone": optic_zone,
        }

        # 커스텀 디자인 생성 - 업로드된 이미지 URL 포함
        created_design = custom_design_crud.create_custom_design(
            db=db,
            form_data=form_data,
            user_id=current_user.username,
            main_image_url=main_image_url  # 업로드된 URL 직접 전달
        )

        return custom_design_schema.CustomDesignCreateResponse(
            id=created_design.id,
            item_name=created_design.item_name,
            main_image_url=created_design.main_image_url or ""
        )

    except Exception as e:
        print(f"커스텀 디자인 생성 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"커스텀 디자인 생성 중 오류가 발생했습니다: {str(e)}"
        )
