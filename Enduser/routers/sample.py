from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from db import models
from core.security import get_current_user
from Enduser.schemas import sample as sample_schema
from Enduser.crud import sample as sample_crud
import math
from datetime import datetime

router = APIRouter(tags=["Sample"])


@router.get("/sample/list", response_model=sample_schema.PaginatedSampleResponse)
def get_sample_list(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        orderBy: Optional[str] = Query("latest", description="정렬 기준 (latest: 최신순-기본값, oldest: 오래된순)"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """샘플 요청 목록 조회 (progressstatus 기반)"""

    paginated_data = sample_crud.get_samples_paginated(
        db=db,
        user_id=current_user.username,
        page=page,
        size=size,
        orderBy=orderBy
    )

    total_count = paginated_data["total_count"]
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    return sample_schema.PaginatedSampleResponse(
        total_count=total_count,
        total_pages=total_pages,
        page=page,
        size=size,
        items=paginated_data["items"]
    )


@router.get("/sample/{progress_id}", response_model=sample_schema.SampleDetailResponse)
def get_sample_detail(
        progress_id: int,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """샘플 요청 항목 정보 조회"""

    sample_detail = sample_crud.get_sample_detail(
        db=db,
        user_id=current_user.username,
        progress_id=progress_id
    )

    if not sample_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 샘플 요청을 찾을 수 없습니다."
        )

    return sample_schema.SampleDetailResponse(**sample_detail)


@router.delete("/sample/{progress_id}", response_model=sample_schema.SampleResultResponse)
def delete_sample_item(
        progress_id: int,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """샘플 요청 항목 단일 삭제 (대기상태만 삭제 가능)"""

    success = sample_crud.delete_sample(
        db=db,
        user_id=current_user.username,
        progress_id=progress_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="대기 상태의 샘플만 삭제할 수 있습니다."
        )

    return sample_schema.SampleResultResponse(result="삭제를 성공했습니다.")


@router.post("/sample/customdesign/{name}", response_model=sample_schema.SampleResultResponse)
def create_sample_from_custom_design(
        name: str,
        client_name: str = Form(...),
        number: str = Form(...),
        address: str = Form(...),
        request_note: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """장바구니의 커스텀디자인을 샘플 요청(progress_status)으로 생성"""

    success = sample_crud.create_progress_status_from_cart(
        db=db,
        user_id=current_user.username,
        item_name=name,
        category='커스텀디자인',
        client_name=client_name,
        number=number,
        address=address,
        request_note=request_note
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장바구니에서 해당 커스텀디자인을 찾을 수 없습니다."
        )

    return sample_schema.SampleResultResponse(result="커스텀 디자인 샘플제작 요청 성공")


@router.post("/sample/portfolio/{name}", response_model=sample_schema.SampleResultResponse)
def create_sample_from_portfolio(
        name: str,
        client_name: str = Form(...),
        number: str = Form(...),
        address: str = Form(...),
        request_note: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """장바구니의 포트폴리오를 샘플 요청(progress_status)으로 생성"""

    success = sample_crud.create_progress_status_from_cart(
        db=db,
        user_id=current_user.username,
        item_name=name,
        category='포트폴리오',
        client_name=client_name,
        number=number,
        address=address,
        request_note=request_note
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장바구니에서 해당 포트폴리오를 찾을 수 없습니다."
        )

    return sample_schema.SampleResultResponse(result="포트폴리오 샘플제작 요청 성공")


@router.post("/sample/customdesign", response_model=sample_schema.BulkSampleResultResponse)
def create_all_samples_from_custom_design(
        client_name: str = Form(...),
        number: str = Form(...),
        address: str = Form(...),
        request_note: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """장바구니의 모든 커스텀디자인을 일괄 샘플 요청"""

    # 카트에서 사용자의 모든 커스텀디자인 가져오기
    cart_items = db.query(models.Cart).filter(
        models.Cart.user_id == current_user.username,
        models.Cart.category == "커스텀디자인"
    ).all()

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장바구니에 커스텀디자인이 없습니다."
        )

    success_count = 0
    failed_items = []

    for cart_item in cart_items:
        try:
            success = sample_crud.create_progress_status_from_cart(
                db=db,
                user_id=current_user.username,
                item_name=cart_item.item_name,
                category='커스텀디자인',
                client_name=client_name,
                number=number,
                address=address,
                request_note=request_note
            )
            if success:
                success_count += 1
            else:
                failed_items.append(cart_item.item_name)
        except Exception as e:
            failed_items.append(cart_item.item_name)

    return sample_schema.BulkSampleResultResponse(
        result=f"커스텀디자인 {success_count}개 샘플 요청 완료",
        success_count=success_count,
        failed_count=len(failed_items),
        failed_items=failed_items
    )


@router.post("/sample/portfolio", response_model=sample_schema.BulkSampleResultResponse)
def create_all_samples_from_portfolio(
        client_name: str = Form(...),
        number: str = Form(...),
        address: str = Form(...),
        request_note: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """장바구니의 모든 포트폴리오를 일괄 샘플 요청"""

    # 카트에서 사용자의 모든 포트폴리오 가져오기
    cart_items = db.query(models.Cart).filter(
        models.Cart.user_id == current_user.username,
        models.Cart.category == "포트폴리오"
    ).all()

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장바구니에 포트폴리오가 없습니다."
        )

    success_count = 0
    failed_items = []

    for cart_item in cart_items:
        try:
            success = sample_crud.create_progress_status_from_cart(
                db=db,
                user_id=current_user.username,
                item_name=cart_item.item_name,
                category='포트폴리오',
                client_name=client_name,
                number=number,
                address=address,
                request_note=request_note
            )
            if success:
                success_count += 1
            else:
                failed_items.append(cart_item.item_name)
        except Exception as e:
            failed_items.append(cart_item.item_name)

    return sample_schema.BulkSampleResultResponse(
        result=f"포트폴리오 {success_count}개 샘플 요청 완료",
        success_count=success_count,
        failed_count=len(failed_items),
        failed_items=failed_items
    )