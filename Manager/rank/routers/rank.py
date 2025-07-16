# rank/routers/rank.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from Manager.rank.crud import rank as rank_crud
from Manager.rank.schemas import rank as rank_schema

router = APIRouter()

@router.get("/v1/rank/", response_model=rank_schema.RankResponse, summary="Get ranking data")
def get_rank_data(db: Session = Depends(get_db)):
    """
    **출시제품, 포트폴리오, 커스텀 디자인, 진행현황에 대한 랭킹 및 상태 정보를 반환합니다.**

    - **released_product**: 조회수(view)가 가장 많은 출시제품 10개를 보여줍니다.
    - **portfolio**: 조회수(view)가 가장 많은 포트폴리오 10개를 보여줍니다.
    - **custom_design**: 커스텀 디자인의 상태별 개수를 보여줍니다. (wait, reject, under_review, complet)
    - **progress_status**: 진행현황의 상태별 개수를 보여줍니다. (wait, pregress, delay, delivery_completed)
    """
    top_released_products = rank_crud.get_top_released_products(db)
    top_portfolios = rank_crud.get_top_portfolios(db)
    custom_design_counts = rank_crud.get_custom_design_status_counts(db)
    progress_status_counts = rank_crud.get_progress_status_counts(db)  # 실제 데이터 사용

    released_product_items = [rank_schema.RankItem(image=p.image, name=p.name, view=p.view) for p in top_released_products]
    portfolio_items = [rank_schema.RankItem(image=p.image, name=p.name, view=p.view) for p in top_portfolios]

    return rank_schema.RankResponse(
        released_product=released_product_items,
        portfolio=portfolio_items,
        custom_design=rank_schema.CustomDesignStatus(**custom_design_counts),
        progress_status=rank_schema.ProgressStatus(**progress_status_counts)  # 실제 데이터 사용
    )