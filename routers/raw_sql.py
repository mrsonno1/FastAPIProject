# routers/raw_sql.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from schemas import raw_sql as sql_schema
from crud import raw_sql as sql_crud
from core.security import get_current_user  # 인증을 위한 의존성
from db import models  # 사용자 모델을 가져오기 위함

router = APIRouter(prefix="/raw-sql", tags=["Raw SQL Execution"])


@router.post("/select", response_model=sql_schema.QueryResult)
def run_select_query(
        sql_query: sql_schema.RawSQLQuery,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)  # 1. 인증된 사용자인지 확인
):
    """
    (주의!) 외부에서 받은 SELECT SQL 쿼리를 직접 실행합니다.
    'admin' 권한을 가진 사용자만 이 API를 호출할 수 있습니다.
    """
    # 2. 'admin' 권한이 있는지 확인
    if current_user.permission not in ['admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 작업을 수행할 권한이 없습니다."
        )

    return sql_crud.execute_select_query(db, query=sql_query.query)


@router.post("/execute", response_model=sql_schema.ExecuteResult)
def run_mutation_query(
        sql_query: sql_schema.RawSQLQuery,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)  # 1. 인증된 사용자인지 확인
):
    """
    (매우 주의!) 외부에서 받은 INSERT, UPDATE, DELETE SQL 쿼리를 직접 실행합니다.
    'admin' 권한을 가진 사용자만 이 API를 호출할 수 있습니다.
    """
    # 2. 'admin' 권한이 있는지 확인
    if current_user.permission not in ['admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 작업을 수행할 권한이 없습니다."
        )

    return sql_crud.execute_mutation_query(db, query=sql_query.query)