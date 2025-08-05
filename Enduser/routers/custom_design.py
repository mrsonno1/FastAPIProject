# Enduser/routers/custom_design.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from db import models
from core.security import get_current_user
from Enduser.schemas import custom_design as custom_design_schema
from Enduser.schemas import base64_upload as base64_schema  # 추가
from Enduser.crud import custom_design as custom_design_crud
import math
from services.storage_service import storage_service
from services.thumbnail_service import thumbnail_service

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
        user_id=current_user.id,  # 현재 사용자 ID 전달
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
    try:
        paginated_data = custom_design_crud.get_user_custom_designs_paginated(
            db=db,
            user_id=current_user.username,
            page=page,
            size=size,
            orderBy=orderBy
        )

        total_count = paginated_data["total_count"]
        total_pages = math.ceil(total_count / size) if total_count > 0 else 1

        # 현재 사용자의 카트에 있는 커스텀디자인 item_name 목록 가져오기
        cart_items = db.query(models.Cart.item_name).filter(
            models.Cart.user_id == current_user.username,
            models.Cart.category == "커스텀디자인"
        ).all()
        cart_item_names = {item[0] for item in cart_items if item[0]}  # None 값 제외

        # 응답 형식에 맞게 변환 (status에 따른 item_name 표시 처리)
        items = []
        for design in paginated_data["items"]:
            # status가 '1' 또는 '2'일 때 item_name을 ""로 표시
            display_item_name = "" if design.status in ['0','1', '2'] else (design.item_name or "")
            
            # 카트에 있는지 확인 (item_name이 None이 아닐 때만)
            in_cart = design.item_name in cart_item_names if design.item_name else False

            items.append(custom_design_schema.CustomDesignListItem(
                id=design.id,
                item_name=display_item_name,
                main_image_url=design.main_image_url or "",
                thumbnail_url=design.thumbnail_url or "",  # thumbnail_url 추가
                in_cart=in_cart,  # in_cart 필드 추가
                account_code=current_user.account_code  # account_code 추가
            ))

        return custom_design_schema.PaginatedCustomDesignResponse(
            total_count=total_count,
            total_pages=total_pages,
            page=page,
            size=size,
            items=items
        )
    except Exception as e:
        print(f"ERROR in get_my_designs_list: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"디자인 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/my-designs/{design_id}", response_model=custom_design_schema.CustomDesignDetailResponse)
def get_my_design_detail(
        design_id: int,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """내 커스텀디자인 항목 조회"""
    try:
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

        # design 상태 확인을 위해 DB에서 디자인 정보 가져오기
        design = custom_design_crud.get_design_by_id(db, design_id, current_user.username)

        # status가 '0', '1' 또는 '2'일 때 item_name을 "-"로 표시
        # status가 '3'이고 item_name이 있을 때만 실제 값 표시
        if design and design.status in ['0', '1', '2']:
            design_detail['item_name'] = "-"
        elif design and design.status == '3' and not design.item_name:
            design_detail['item_name'] = "-"  # status 3이지만 아직 item_name이 없는 경우
        
        # account_code 추가
        design_detail['account_code'] = current_user.account_code

        # CustomDesignDetailResponse 스키마에 맞게 데이터 변환
        response_data = {
            "item_name": design_detail.get('item_name'),
            "account_code": design_detail.get('account_code', current_user.account_code),
            "design_line": design_detail.get('design_line'),
            "design_base1": design_detail.get('design_base1'),
            "design_base2": design_detail.get('design_base2'),
            "design_pupil": design_detail.get('design_pupil'),
            "graphic_diameter": design_detail.get('graphic_diameter'),
            "optic_zone": design_detail.get('optic_zone'),
            "dia": design_detail.get('dia')
        }

        return custom_design_schema.CustomDesignDetailResponse(**response_data)
    except Exception as e:
        print(f"ERROR in get_my_design_detail: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"디자인 조회 중 오류가 발생했습니다: {str(e)}"
        )


# 기존 Form/File 업로드 방식 (하위 호환성 유지)
@router.post("/my-designs", response_model=custom_design_schema.CustomDesignCreateResponse)
def create_my_design(
        # Form 데이터로 받기 (item_name 제거 - 자동생성)
        design_line_image_id: Optional[str] = Form(None, description="라인 이미지 ID"),
        design_line_color_id: Optional[str] = Form(None, description="라인 색상 ID"),
        line_transparency: Optional[str] = Form("100", description="라인 투명도"),
        line_size: Optional[str] = Form("100", description="라인 크기"),
        design_base1_image_id: Optional[str] = Form(None, description="바탕1 이미지 ID"),
        design_base1_color_id: Optional[str] = Form(None, description="바탕1 색상 ID"),
        base1_transparency: Optional[str] = Form("100", description="바탕1 투명도"),
        base1_size: Optional[str] = Form("100", description="바탕1 크기"),
        design_base2_image_id: Optional[str] = Form(None, description="바탕2 이미지 ID"),
        design_base2_color_id: Optional[str] = Form(None, description="바탕2 색상 ID"),
        base2_transparency: Optional[str] = Form("100", description="바탕2 투명도"),
        base2_size: Optional[str] = Form("100", description="바탕2 크기"),
        design_pupil_image_id: Optional[str] = Form(None, description="동공 이미지 ID"),
        design_pupil_color_id: Optional[str] = Form(None, description="동공 색상 ID"),
        pupil_transparency: Optional[str] = Form("100", description="동공 투명도"),
        pupil_size: Optional[str] = Form("100", description="동공 크기"),
        graphic_diameter: Optional[str] = Form(None, description="그래픽 직경"),
        optic_zone: Optional[str] = Form(None, description="옵틱 존"),
        dia: Optional[str] = Form(None, description="DIA"),
        request_message: Optional[str] = Form(None, description="요청 메시지"),
        file: Optional[UploadFile] = File(None, description="메인 이미지 파일"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """커스텀디자인 완료 목록 추가 - File 업로드 방식"""

    # 초기 생성 시에는 item_name을 null로 설정
    # status가 3(완료)로 변경될 때 account_code 기반으로 생성
    item_name = None

    # 파일 업로드 처리
    main_image_url = None
    thumbnail_url = None
    if file:
        try:
            print(f"DEBUG: File received - filename: {file.filename}, content_type: {file.content_type}")
            
            # 파일 내용을 먼저 읽어서 저장
            file_content = file.file.read()
            print(f"DEBUG: File content read - size: {len(file_content)} bytes")
            
            file.file.seek(0)  # 파일 포인터를 처음으로 되돌림
            
            upload_result = storage_service.upload_file(file)
            if not upload_result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="이미지 업로드에 실패했습니다."
                )
            main_image_url = upload_result["public_url"]
            print(f"DEBUG: Main image uploaded - URL: {main_image_url}")
            
            # Generate thumbnail
            if file_content:
                print(f"DEBUG: Creating thumbnail for {file.filename}")
                thumbnail_url = thumbnail_service.create_and_upload_thumbnail(file_content, file.filename)
                print(f"DEBUG: Thumbnail result - URL: {thumbnail_url}")
            else:
                print("ERROR: File content is empty, cannot create thumbnail")
            
            # 디버깅을 위한 로그
            print(f"DEBUG: Final results - main_image_url: {main_image_url}, thumbnail_url: {thumbnail_url}")
        except Exception as e:
            print(f"ERROR: File upload failed - {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"이미지 업로드 중 오류가 발생했습니다: {str(e)}"
            )
    else:
        print("DEBUG: No file provided in request")

    try:
        form_data = {
            "item_name": item_name,  # null로 설정
            "request_message": request_message,
            "design_line_image_id": design_line_image_id,
            "design_line_color_id": design_line_color_id,
            "line_transparency": line_transparency,
            "line_size": line_size,
            "design_base1_image_id": design_base1_image_id,
            "design_base1_color_id": design_base1_color_id,
            "base1_transparency": base1_transparency,
            "base1_size": base1_size,
            "design_base2_image_id": design_base2_image_id,
            "design_base2_color_id": design_base2_color_id,
            "base2_transparency": base2_transparency,
            "base2_size": base2_size,
            "design_pupil_image_id": design_pupil_image_id,
            "design_pupil_color_id": design_pupil_color_id,
            "pupil_transparency": pupil_transparency,
            "pupil_size": pupil_size,
            "graphic_diameter": graphic_diameter,
            "optic_zone": optic_zone,
            "dia": dia,
        }

        created_design = custom_design_crud.create_custom_design(
            db=db,
            form_data=form_data,
            user_id=current_user.username,
            main_image_url=main_image_url,
            thumbnail_url=thumbnail_url
        )

        return custom_design_schema.CustomDesignCreateResponse(
            id=created_design.id,
            item_name=created_design.item_name,
            main_image_url=created_design.main_image_url or ""
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"커스텀 디자인 생성 중 오류가 발생했습니다: {str(e)}"
        )


# 새로운 Base64 업로드 방식
@router.post("/my-designs/base64", response_model=custom_design_schema.CustomDesignCreateResponse)
def create_my_design_base64(
        design_data: base64_schema.CustomDesignCreateWithBase64,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """커스텀디자인 완료 목록 추가 - Base64 업로드 방식 (Unity용)"""

    # 초기 생성 시에는 item_name을 null로 설정
    # status가 3(완료)로 변경될 때 account_code 기반으로 생성
    item_name = None

    # Base64 이미지 업로드 처리
    main_image_url = None
    thumbnail_url = None
    if design_data.main_image:
        try:
            # Base64 데이터를 바이트로 변환
            image_bytes = design_data.main_image.to_bytes()

            # Storage Service를 통해 업로드
            upload_result = storage_service.upload_base64_file(
                file_data=image_bytes,
                filename=design_data.main_image.filename,
                content_type=design_data.main_image.content_type
            )

            if not upload_result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="이미지 업로드에 실패했습니다."
                )

            main_image_url = upload_result["public_url"]
            
            # Generate thumbnail
            thumbnail_url = thumbnail_service.create_and_upload_thumbnail(
                image_bytes, 
                design_data.main_image.filename
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"이미지 업로드 중 오류가 발생했습니다: {str(e)}"
            )

    try:
        # Form 데이터 구성
        form_data = {
            "item_name": item_name,  # null로 설정
            "request_message": getattr(design_data, 'request_message', None),
            "design_line_image_id": design_data.design_line_image_id,
            "design_line_color_id": design_data.design_line_color_id,
            "line_transparency": design_data.line_transparency,
            "line_size": design_data.line_size,
            "design_base1_image_id": design_data.design_base1_image_id,
            "design_base1_color_id": design_data.design_base1_color_id,
            "base1_transparency": design_data.base1_transparency,
            "base1_size": design_data.base1_size,
            "design_base2_image_id": design_data.design_base2_image_id,
            "design_base2_color_id": design_data.design_base2_color_id,
            "base2_transparency": design_data.base2_transparency,
            "base2_size": design_data.base2_size,
            "design_pupil_image_id": design_data.design_pupil_image_id,
            "design_pupil_color_id": design_data.design_pupil_color_id,
            "pupil_transparency": design_data.pupil_transparency,
            "pupil_size": design_data.pupil_size,
            "graphic_diameter": design_data.graphic_diameter,
            "optic_zone": design_data.optic_zone,
            "dia": getattr(design_data, 'dia', None),
        }

        # 커스텀 디자인 생성
        created_design = custom_design_crud.create_custom_design(
            db=db,
            form_data=form_data,
            user_id=current_user.username,
            main_image_url=main_image_url,
            thumbnail_url=thumbnail_url
        )

        return custom_design_schema.CustomDesignCreateResponse(
            id=created_design.id,
            item_name=created_design.item_name,
            main_image_url=created_design.main_image_url or ""
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"커스텀 디자인 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.patch("/my-designs/{design_id}/status")
def update_design_status(
        design_id: int,
        status: str = Form(..., description="상태값 (0: 대기, 1: 진행중, 2: 보류, 3: 완료)"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """커스텀 디자인 상태 업데이트 - status가 3일 때 item_name 자동 생성"""
    
    # 상태값 유효성 검사
    valid_statuses = ['0', '1', '2', '3']
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"유효하지 않은 상태값입니다. 가능한 값: {', '.join(valid_statuses)}"
        )
    
    # 상태 업데이트
    updated_design = custom_design_crud.update_design_status(
        db=db,
        design_id=design_id,
        user_id=current_user.username,
        status=status
    )
    
    if not updated_design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="커스텀 디자인을 찾을 수 없습니다."
        )
    
    return {
        "success": True,
        "message": f"상태가 {status}로 업데이트되었습니다.",
        "data": {
            "id": updated_design.id,
            "item_name": updated_design.item_name,
            "status": updated_design.status
        }
    }
