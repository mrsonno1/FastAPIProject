from sqlalchemy.orm import Session
from db import models
from Manager.portfolio.schemas import portfolio as portfolio_schema
from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from datetime import date
from Manager.progress_status.crud import progress_status as progress_status_crud


def create_portfolio(db: Session, portfolio: portfolio_schema.PortfolioCreate, user_id: int):

    if portfolio.is_fixed_axis not in ['Y', 'N']:
        raise HTTPException(status_code=400, detail="is_fixed_axis는 'Y' 또는 'N'이어야 합니다")

    db_portfolio = models.Portfolio(
        design_name=portfolio.design_name,
        color_name=portfolio.color_name,
        exposed_countries=portfolio.exposed_countries,
        is_fixed_axis=portfolio.is_fixed_axis,
        main_image_url=portfolio.main_image_url,
        design_line_image_id=portfolio.design_line_image_id,
        design_line_color_id=portfolio.design_line_color_id,
        design_base1_image_id=portfolio.design_base1_image_id,
        design_base1_color_id=portfolio.design_base1_color_id,
        design_base2_image_id=portfolio.design_base2_image_id,
        design_base2_color_id=portfolio.design_base2_color_id,
        design_pupil_image_id=portfolio.design_pupil_image_id,
        design_pupil_color_id=portfolio.design_pupil_color_id,
        graphic_diameter=portfolio.graphic_diameter,
        optic_zone=portfolio.optic_zone,
        user_id=user_id
    )

    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)

    # 포트폴리오 생성 후 progress_status 생성/업데이트
    # 해당 사용자의 가장 최근 custom_design 찾기
    user = db.query(models.AdminUser).filter(models.AdminUser.id == user_id).first()
    if user:
        latest_design = db.query(models.CustomDesign).filter(
            models.CustomDesign.user_id == user.username
        ).order_by(models.CustomDesign.created_at.desc()).first()

        if latest_design:
            progress_status_crud.create_progress_status_for_portfolio(
                db=db,
                portfolio_id=db_portfolio.id,
                custom_design_id=latest_design.id,
                user_id=user_id
            )

    return db_portfolio


# 디자인명 중복 체크
def get_portfolio_by_design_name(db: Session, design_name: str):
    return db.query(models.Portfolio).filter(models.Portfolio.design_name == design_name).first()


def delete_portfolio_by_id(db: Session, portfolio_id: int) -> bool:
    db_portfolio = db.query(models.Portfolio).filter(models.Portfolio.id == portfolio_id, models.Portfolio.is_deleted == False).first()
    if not db_portfolio:
        return False

    # Check if the main_image_url is referenced in the Image model
    if db_portfolio.main_image_url and db.query(models.Image).filter(models.Image.public_url == db_portfolio.main_image_url).first():
        raise HTTPException(status_code=400, detail=f"Portfolio '{db_portfolio.design_name}' cannot be deleted as its main image is referenced elsewhere.")

    db_portfolio.is_deleted = True
    db.commit()
    return True


def get_all_portfolio(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Portfolio).order_by(models.Portfolio.id.desc()).offset(skip).limit(limit).all()



def update_portfolio(
        db: Session,
        db_portfolio: models.Portfolio,
        portfolio_update: portfolio_schema.PortfolioCreate
):
    update_data = portfolio_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_portfolio, key, value)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


def get_portfolios_paginated(
        db: Session,
        page: int,
        size: int,
        design_name: Optional[str] = None,
        color_name: Optional[str] = None,
        exposed_countries: Optional[List[str]] = None,
        is_fixed_axis: Optional[str] = None,
        orderBy: Optional[str] = None,
):
    query = db.query(models.Portfolio, models.AdminUser).join(
        models.AdminUser,
        models.Portfolio.user_id == models.AdminUser.id,

    )

    query = query.filter( models.Portfolio.is_deleted == False)
    if design_name:
        query = query.filter(models.Portfolio.design_name.ilike(f"%{design_name}%"))

    if color_name:
        query = query.filter(models.Portfolio.color_name.ilike(f"%{color_name}%"))

    if exposed_countries:
        # 각 국가 ID가 콤마로 구분된 리스트에 포함되어 있는지 확인
        for country_id in exposed_countries:
            query = query.filter(models.Portfolio.exposed_countries.like(f"%{country_id}%"))

    if is_fixed_axis is not None:
        query = query.filter(models.Portfolio.is_fixed_axis == is_fixed_axis)

    if orderBy:
        try:
            # 1. '컬럼명 방향'으로 문자열을 분리
            order_column_name, order_direction = orderBy.strip().split()

            # 2. 허용할 컬럼 목록 정의 (보안 및 안정성)
            allowed_columns = {
                "design_name": models.Portfolio.design_name,
                "created_at": models.Portfolio.created_at,
                "views": models.Portfolio.views,
                "id": models.Portfolio.id  # 기본 정렬을 위해 id도 포함
            }

            # 3. 허용된 컬럼인지 확인
            if order_column_name in allowed_columns:
                order_column = allowed_columns[order_column_name]

                # 4. 정렬 방향 적용
                if order_direction.lower() == 'desc':
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column.asc())
            else:
                # 허용되지 않은 컬럼명이면 기본 정렬 적용
                query = query.order_by(models.Portfolio.created_at.desc())

        except (ValueError, AttributeError):
            # orderBy 형식이 잘못되었거나 존재하지 않는 컬럼일 경우 기본 정렬로 대체
            query = query.order_by(models.Portfolio.created_at.desc())
    else:
        # orderBy 파라미터가 없으면 기본 정렬 (최신순)
        query = query.order_by(models.Portfolio.created_at.desc())

    total_count = query.count()
    offset = (page - 1) * size
    results = query.order_by(models.Portfolio.created_at.desc()).offset(offset).limit(size).all()

    # --- 5. 결과를 새로운 형식에 맞게 가공 ---
    formatted_items = []

    # --- 결과를 새로운 형식에 맞게 가공 ---
    # 모든 필요한 ID를 먼저 수집 (N+1 문제 최적화)
    all_image_ids = set()
    all_color_ids = set()
    all_country_ids = set()
    for portfolio, user in results:
        all_image_ids.update(filter(None, [
            portfolio.design_line_image_id, portfolio.design_base1_image_id,
            portfolio.design_base2_image_id, portfolio.design_pupil_image_id
        ]))
        all_color_ids.update(filter(None, [
            portfolio.design_line_color_id, portfolio.design_base1_color_id,
            portfolio.design_base2_color_id, portfolio.design_pupil_color_id
        ]))
        if portfolio.exposed_countries:
            all_country_ids.update(id.strip() for id in portfolio.exposed_countries.split(',') if id.strip())

    # ID를 한 번에 조회하여 딕셔너리로 만듦
    images_map = {str(img.id): img for img in
                  db.query(models.Image).filter(models.Image.id.in_(list(all_image_ids))).all()}
    colors_map = {str(col.id): col for col in
                  db.query(models.Color).filter(models.Color.id.in_(list(all_color_ids))).all()}
    countries_map = {str(c.id): c.country_name for c in
                     db.query(models.Country).filter(models.Country.id.in_(list(all_country_ids))).all()}

    # 헬퍼 함수
    def get_country_names(ids_str):
        if not ids_str: return ""
        names = [countries_map.get(id.strip()) for id in ids_str.split(',') if id.strip()]
        return ", ".join(filter(None, names))

    for portfolio, user in results:
        portfolio.user_name = user.contact_name or user.username
        portfolio.exposed_countries = portfolio.exposed_countries
        portfolio.view_count = portfolio.views
        portfolio.design_line = images_map.get(portfolio.design_line_image_id)
        portfolio.design_line_color = colors_map.get(portfolio.design_line_color_id)
        portfolio.design_base1 = images_map.get(portfolio.design_base1_image_id)
        portfolio.design_base1_color = colors_map.get(portfolio.design_base1_color_id)
        portfolio.design_base2 = images_map.get(portfolio.design_base2_image_id)
        portfolio.design_base2_color = colors_map.get(portfolio.design_base2_color_id)
        portfolio.design_pupil = images_map.get(portfolio.design_pupil_image_id)
        portfolio.design_pupil_color = colors_map.get(portfolio.design_pupil_color_id)

    formatted_items = [p for p, u in results]

    return {"items": formatted_items, "total_count": total_count}

# --- [새로운 상세 정보 조회 함수 추가] ---
def get_portfolio_detail(db: Session, portfolio_id: int) -> Optional[Dict[str, Any]]:
    """ID로 단일 포트폴리오의 상세 정보를 조회합니다."""
    result = db.query(models.Portfolio, models.AdminUser).join(
        models.AdminUser, models.Portfolio.user_id == models.AdminUser.id
    ).filter(models.Portfolio.id == portfolio_id, models.Portfolio.is_deleted == False,).first()



    if not result:
        return None

    portfolio, user = result


    # 조회수 증가 로직
    db.query(models.Portfolio).filter(models.Portfolio.id == portfolio_id).update(
        {models.Portfolio.views: models.Portfolio.views + 1},
        synchronize_session=False,

    )
    # DailyView 기록 로직
    today = date.today()

    daily_view = db.query(models.DailyView).filter(
        models.DailyView.view_date == today,
        models.DailyView.content_type == 'portfolio',
        models.DailyView.content_id == portfolio_id
    ).first()

    if daily_view:
        # 데이터가 있으면 view_count를 1 증가
        daily_view.view_count += 1
    else:
        # 데이터가 없으면 새로 생성
        new_daily_view = models.DailyView(
            view_date=today,
            content_type='portfolio',
            content_id=portfolio_id,
            view_count=1
        )
        db.add(new_daily_view)

    db.commit()
    db.refresh(portfolio)

    # 헬퍼 함수 정의
    def get_image_details(image_id: Optional[str]):
        if not image_id: return None
        image = db.query(models.Image).filter(models.Image.id == image_id).first()
        return image

    def get_color_details(color_id: Optional[str]):
        if not color_id: return None
        color = db.query(models.Color).filter(models.Color.id == color_id).first()
        return color

    def get_country_names(country_ids_str: str):
        if not country_ids_str: return ""
        country_ids = [cid.strip() for cid in country_ids_str.split(',') if cid.strip()]
        if not country_ids: return ""
        countries = db.query(models.Country.country_name).filter(models.Country.id.in_(country_ids)).all()
        return ", ".join([name for name, in countries])

    # 관련 객체들을 portfolio 객체에 동적으로 추가
    portfolio.user_name = user.contact_name or user.username
    portfolio.exposed_countries = portfolio.exposed_countries
    portfolio.view_count = portfolio.views  # 스키마 필드명에 맞게 값 할당
    portfolio.design_line = get_image_details(portfolio.design_line_image_id)
    portfolio.design_line_color = get_color_details(portfolio.design_line_color_id)
    portfolio.design_base1 = get_image_details(portfolio.design_base1_image_id)
    portfolio.design_base1_color = get_color_details(portfolio.design_base1_color_id)
    portfolio.design_base2 = get_image_details(portfolio.design_base2_image_id)
    portfolio.design_base2_color = get_color_details(portfolio.design_base2_color_id)
    portfolio.design_pupil = get_image_details(portfolio.design_pupil_image_id)
    portfolio.design_pupil_color = get_color_details(portfolio.design_pupil_color_id)


    return portfolio
