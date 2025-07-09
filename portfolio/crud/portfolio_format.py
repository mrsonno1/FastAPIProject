from sqlalchemy.orm import Session
from db import models
from portfolio.schemas import portfolio_format
from typing import Optional, List
from sqlalchemy import func
import datetime

def get_image_display_name(db: Session, image_id: str) -> Optional[str]:
    """이미지 ID로 이미지의 display_name을 조회"""
    if not image_id:
        return None

    image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if image:
        return image.display_name
    return None

def get_image_public_url(db: Session, image_id: str) -> Optional[str]:
    """이미지 ID로 이미지의 public_url을 조회"""
    if not image_id:
        return None

    image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if image:
        return image.public_url
    return None

def get_color_name(db: Session, color_id: str) -> Optional[str]:
    """컬러 ID로 컬러의 이름을 조회"""
    if not color_id:
        return None

    color = db.query(models.Color).filter(models.Color.id == color_id).first()
    if color:
        return color.color_name
    return None

def get_color_rgb_values(db: Session, color_id: str) -> Optional[str]:
    """컬러 ID로 RGB 값을 조회하여 처음 3개 값만 반환"""
    if not color_id:
        return None

    color = db.query(models.Color).filter(models.Color.id == color_id).first()
    if color and color.color_values:
        values = color.color_values.split(',')
        if len(values) >= 3:
            return f"{values[0]},{values[1]},{values[2]}"
    return None

def get_country_names(db: Session, country_ids: str) -> str:
    """국가 ID 목록을 국가명 목록으로 변환"""
    if not country_ids:
        return ""

    country_id_list = [id.strip() for id in country_ids.split(',') if id.strip()]
    if not country_id_list:
        return ""

    countries = db.query(models.Country)\
                .filter(models.Country.id.in_(country_id_list))\
                .all()

    return ", ".join([country.country_name for country in countries])

def format_date(date_obj: datetime.datetime) -> str:
    """날짜를 YY/MM/DD 형식으로 포맷팅"""
    if not date_obj:
        return ""
    return date_obj.strftime("%y/%m/%d")

def get_portfolios_formatted(
        db: Session,
        page: int,
        size: int,
        design_name: Optional[str] = None,
        color_name: Optional[str] = None,
        exposed_countries: Optional[List[str]] = None,
        is_fixed_axis: Optional[str] = None,
        orderBy: Optional[str] = None
):

    query = db.query(models.Portfolio)

    # 필터링 로직
    if design_name:
        query = query.filter(models.Portfolio.design_name.ilike(f"%{design_name}%"))

    if color_name:
        query = query.filter(models.Portfolio.color_name.ilike(f"%{color_name}%"))

    if exposed_countries:
        for country_id in exposed_countries:
            query = query.filter(models.Portfolio.exposed_countries.like(f"%{country_id}%"))

    if is_fixed_axis is not None:
        query = query.filter(models.Portfolio.is_fixed_axis == is_fixed_axis)

    # 정렬 로직
    if orderBy:
        try:
            order_column, order_direction = orderBy.split()
            if order_column == "design_name":
                if order_direction.lower() == "asc":
                    query = query.order_by(models.Portfolio.design_name.asc())
                else:
                    query = query.order_by(models.Portfolio.design_name.desc())
            else:
                # 기본 정렬
                query = query.order_by(models.Portfolio.id.desc())
        except ValueError:
            query = query.order_by(models.Portfolio.id.desc())
    else:
        query = query.order_by(models.Portfolio.id.desc())

    # 카운트 및 페이지네이션
    total_count = query.count()
    offset = (page - 1) * size
    portfolios = query.offset(offset).limit(size).all()

    # 포맷팅된 결과 생성
    formatted_items = []
    itemcount = 1
    for idx, portfolio in enumerate(portfolios):
        # 이미지 이름 조회
        line_image_name = get_image_display_name(db, portfolio.design_line_image_id)
        base1_image_name = get_image_display_name(db, portfolio.design_base1_image_id)
        base2_image_name = get_image_display_name(db, portfolio.design_base2_image_id)
        pupil_image_name = get_image_display_name(db, portfolio.design_pupil_image_id)

        # 컬러 이름 조회
        line_color_name = get_color_name(db, portfolio.design_line_color_id)
        base1_color_name = get_color_name(db, portfolio.design_base1_color_id)
        base2_color_name = get_color_name(db, portfolio.design_base2_color_id)
        pupil_color_name = get_color_name(db, portfolio.design_pupil_color_id)

        # RGB 값 조회
        line_rgb = get_color_rgb_values(db, portfolio.design_line_color_id)
        base1_rgb = get_color_rgb_values(db, portfolio.design_base1_color_id)
        base2_rgb = get_color_rgb_values(db, portfolio.design_base2_color_id)
        pupil_rgb = get_color_rgb_values(db, portfolio.design_pupil_color_id)

        # 국가명 변환
        country_names = get_country_names(db, portfolio.exposed_countries)

        # 뷰 카운트 (현재는 정적 값 사용)
        view_count = 0

        # 포맷팅된 아이템 생성
        formatted_item = portfolio_format.PortfolioListItem(
            no=itemcount,
            image=portfolio.main_image_url,
            designName=portfolio.design_name,
            colorName=portfolio.color_name,
            design=portfolio_format.DesignComponents(
                라인='L-'+line_image_name,
                바탕1='B1-'+base1_image_name,
                바탕2='B2-'+base2_image_name,
                동공='H-'+pupil_image_name
            ),
            dkColor=[
                'C-'+line_color_name or "",
                'C-'+base1_color_name or "",
                'C-'+base2_color_name or "",
                'C-'+pupil_color_name or ""
            ],
            dkrgb=[
                line_rgb or "",
                base1_rgb or "",
                base2_rgb or "",
                pupil_rgb or ""
            ],
            diameter=portfolio_format.DiameterInfo(
                G_DIA=portfolio.graphic_diameter,
                Optic=portfolio.optic_zone
            ),
            country=portfolio.exposed_countries,
            fixed=portfolio.is_fixed_axis,
            viewCount=view_count,
            registerDate=format_date(portfolio.created_at)
        )
        itemcount = itemcount +1
        formatted_items.append(formatted_item)

    return {
        "items": formatted_items,
        "total_count": total_count
    }


def get_portfolio_detail(db: Session, portfolio_id: int):

    """단일 포트폴리오 상세 정보를 조회합니다."""

    portfolio = db.query(models.Portfolio).filter(models.Portfolio.id == portfolio_id).first()
    if not portfolio:
        return None

    # 이미지 이름 조회
    line_image_name = get_image_display_name(db, portfolio.design_line_image_id)
    base1_image_name = get_image_display_name(db, portfolio.design_base1_image_id)
    base2_image_name = get_image_display_name(db, portfolio.design_base2_image_id)
    pupil_image_name = get_image_display_name(db, portfolio.design_pupil_image_id)

    # 이미지 URL 조회
    line_image_url = get_image_public_url(db, portfolio.design_line_image_id)
    base1_image_url = get_image_public_url(db, portfolio.design_base1_image_id)
    base2_image_url = get_image_public_url(db, portfolio.design_base2_image_id)
    pupil_image_url = get_image_public_url(db, portfolio.design_pupil_image_id)

    # 컬러 이름 조회
    line_color_name = get_color_name(db, portfolio.design_line_color_id)
    base1_color_name = get_color_name(db, portfolio.design_base1_color_id)
    base2_color_name = get_color_name(db, portfolio.design_base2_color_id)
    pupil_color_name = get_color_name(db, portfolio.design_pupil_color_id)

    # RGB 값 조회
    line_rgb = get_color_rgb_values(db, portfolio.design_line_color_id)
    base1_rgb = get_color_rgb_values(db, portfolio.design_base1_color_id)
    base2_rgb = get_color_rgb_values(db, portfolio.design_base2_color_id)
    pupil_rgb = get_color_rgb_values(db, portfolio.design_pupil_color_id)

    # 포맷팅된 응답 생성
    from portfolio.schemas import portfolio_format

    detail_item = portfolio_format.PortfolioDetailItem(
        designName=portfolio.design_name,
        colorName=portfolio.color_name,
        country=portfolio.exposed_countries,  # 원본 국가 ID 문자열 그대로 사용
        fixed=portfolio.is_fixed_axis,
        image=portfolio.main_image_url,
        design=portfolio_format.DesignComponents(
            라인='L-'+line_image_name,
            바탕1='B1-'+base1_image_name,
            바탕2='B2-'+base2_image_name,
            동공='H-'+pupil_image_name
        ),
        designimage=[
            line_image_url or "",
            base1_image_url or "",
            base2_image_url or "",
            pupil_image_url or ""
        ],
        dkColor=[
            'C-'+line_color_name or "",
            'C-'+base1_color_name or "",
            'C-'+base2_color_name or "",
            'C-'+pupil_color_name or ""
        ],
        dkrgb=[
            line_rgb or "",
            base1_rgb or "",
            base2_rgb or "",
            pupil_rgb or ""
        ],
        G_DIA=portfolio.graphic_diameter,
        Optic=portfolio.optic_zone
    )

    return detail_item
