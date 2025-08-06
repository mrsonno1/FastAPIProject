from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from Manager.custom_design.crud import custom_design as custom_design_CRUD
import math # math 임포트
from db.database import get_db
from Manager.custom_design.schemas import custom_design as custom_design_schema
from db import models
from core.security import get_current_user # 인증 의존성 임포트
from typing import Optional # Optional 임포트
from Manager.portfolio.schemas import portfolio as portfolio_schema
from services.storage_service import storage_service

router = APIRouter(prefix="/custom-designs", tags=["Custom Designs"])



# Manager/custom_design/routers/custom_design.py (일부분만)
@router.post("/", response_model=custom_design_schema.CustomDesignApiResponse,
             status_code=status.HTTP_201_CREATED)
def create_new_custom_design(
    request_message: Optional[str] = Form(None),
    main_image_file: Optional[UploadFile] = File(None),  # 파일은 File()로 받음
    design_line_image_id: Optional[str] = Form(None),
    design_line_color_id: Optional[str] = Form(None),
    design_base1_image_id: Optional[str] = Form(None),
    design_base1_color_id: Optional[str] = Form(None),
    design_base2_image_id: Optional[str] = Form(None),
    design_base2_color_id: Optional[str] = Form(None),
    design_pupil_image_id: Optional[str] = Form(None),
    design_pupil_color_id: Optional[str] = Form(None),
    line_transparency: Optional[str] = Form(None),
    base1_transparency: Optional[str] = Form(None),
    base2_transparency: Optional[str] = Form(None),
    pupil_transparency: Optional[str] = Form(None),
    line_size: Optional[str] = Form(None),
    base1_size: Optional[str] = Form(None),
    base2_size: Optional[str] = Form(None),
    pupil_size: Optional[str] = Form(None),
    graphic_diameter: Optional[str] = Form(None),
    optic_zone: Optional[str] = Form(None),
    dia: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):
    """커스텀 디자인 요청 생성 - 요청 시에는 코드를 생성하지 않음"""
    # 코드 생성 없이 None으로 설정
    new_code = None

    # --- 메인 이미지 파일 처리 ---
    main_image_url = None
    if main_image_file:
        upload_result = storage_service.upload_file(main_image_file)
        if not upload_result:
            raise HTTPException(status_code=500, detail="메인 이미지 업로드에 실패했습니다.")
        main_image_url = upload_result["public_url"]

    try:
        # --- 받은 Form 데이터로 Pydantic 모델 객체 생성 ---
        design_data = custom_design_schema.CustomDesignCreate(
            item_name=new_code,
            request_message=request_message,
            main_image_url=main_image_url,
            design_line_image_id=design_line_image_id,
            design_line_color_id=design_line_color_id,
            design_base1_image_id=design_base1_image_id,
            design_base1_color_id=design_base1_color_id,
            design_base2_image_id=design_base2_image_id,
            design_base2_color_id=design_base2_color_id,
            design_pupil_image_id=design_pupil_image_id,
            design_pupil_color_id=design_pupil_color_id,
            line_transparency=line_transparency,
            base1_transparency=base1_transparency,
            base2_transparency=base2_transparency,
            pupil_transparency=pupil_transparency,
            line_size=line_size,
            base1_size=base1_size,
            base2_size=base2_size,
            pupil_size=pupil_size,
            graphic_diameter=graphic_diameter,
            optic_zone=optic_zone,
            dia=dia
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"데이터 유효성 검사 실패: {e}")

    # --- CRUD 함수 호출 방식 변경 ---
    # 이제 'code' 파라미터는 필요 없고, Pydantic 모델 객체를 전달합니다.
    created_customdesign = custom_design_CRUD.create_design(
        db=db,
        design=design_data,
        user_id=current_user.username
    )

    response_data = custom_design_schema.CustomDesignResponse.model_validate(created_customdesign)

    return custom_design_schema.CustomDesignApiResponse(
        success=True,
        message="커스텀디자인이 성공적으로 생성되었습니다.",
        data=response_data
    )


@router.patch("/status/{design_id}",
              response_model=custom_design_schema.CustomDesignApiResponse)
def update_custom_design_details(
        design_id: int,
        # 폼 필드들
        status: str = Form(...),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """ID로 특정 커스텀 디자인의 정보를 업데이트합니다."""

    db_design = custom_design_CRUD.get_design_by_id(db, design_id)
    if not db_design:
        raise HTTPException(status_code=404, detail="수정할 커스텀 디자인을 찾을 수 없습니다.")


    # 업데이트할 데이터만 담은 딕셔너리 생성
    update_data = {
        "status": status
    }
    # None이 아닌 값들만 필터링하여 실제 업데이트할 데이터만 남김
    update_data_filtered = {k: v for k, v in update_data.items() if v is not None}

    # CRUD 업데이트 함수 호출
    updated_design = custom_design_CRUD.update_design(
        db, db_design=db_design, update_data=update_data_filtered
    )

    response_data = custom_design_schema.CustomDesignResponse.model_validate(updated_design)

    return custom_design_schema.CustomDesignApiResponse(
        success=True,
        message="커스텀 디자인이 성공적으로 업데이트되었습니다.",
        data=response_data
    )


@router.get("/list", response_model=custom_design_schema.PaginatedCustomDesignResponse)
def read_all_custom_designs(
        # 페이지네이션 파라미터
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),

        # 검색 필터 파라미터
        item_name: Optional[str] = Query(None, description="코드명으로 검색"),
        user_name: Optional[str] = Query(None, description="아이디로 검색"),
        status: Optional[str] = Query(None, description="상태값"),

        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):

    """
    모든 커스텀 디자인 목록을 검색 조건과 함께 페이지네이션하여 조회합니다.
    """
    paginated_data = custom_design_CRUD.get_designs_paginated(
        db,
        page=page,
        size=size,
        item_name=item_name,
        user_name=user_name,
        status=status
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


# --- [새로운 상세 정보 조회 엔드포인트 추가] ---
@router.get("/info/{design_id}", response_model=custom_design_schema.CustomDesignDetailResponse)
def get_custom_design_detail(
        design_id: int,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """ID로 커스텀 디자인의 상세 정보를 포맷에 맞게 조회합니다."""
    try:
        detail_data = custom_design_CRUD.get_design_detail_formatted(db, design_id=design_id)

        if not detail_data:
            raise HTTPException(status_code=404, detail="해당 ID의 커스텀 디자인을 찾을 수 없습니다.")

        return detail_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_custom_design_detail: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"커스텀 디자인 상세 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/{design_id}", response_model=portfolio_schema.StatusResponse,
               status_code=status.HTTP_200_OK)
def delete_single_custom_design(
    design_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):
    """ID로 특정 커스텀 디자인을 삭제합니다."""
    try:
        was_deleted = custom_design_CRUD.delete_custom_design_by_id(db, design_id=design_id)
        if not was_deleted:
            raise HTTPException(status_code=404, detail="해당 ID의 커스텀 디자인을 찾을 수 없습니다.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"An unexpected error occurred: {e}")

    return portfolio_schema.StatusResponse(status="success",
                                           message="커스텀 디자인이 성공적으로 삭제되었습니다.")


@router.get("/{design_id}", response_model=custom_design_schema.CustomDesignResponse)
def read_single_custom_design(design_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):

    db_design = custom_design_CRUD.get_design_by_id(db, design_id)
    if db_design is None:
        raise HTTPException(status_code=404, detail="디자인을 찾을 수 없습니다.")
    return db_design
