# Manager/admin/routers/database.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from typing import List, Dict, Any, Optional
from db.database import get_db, engine
from db import models
from core.security import get_current_user
import json
from datetime import datetime, date

router = APIRouter(
    prefix="/admin/database",  # prefix 수정 주의
    tags=["Database Management"],
)

# 수정 가능한 테이블 목록 (보안상 중요한 테이블은 제외)
ALLOWED_TABLES = [
    'brands', 'countries', 'images', 'colors',
    'custom_designs', 'portfolios', 'releasedproducts',
    'progressstatus', 'carts', 'shares', 'realtime_users',
    'daily_views'
]

# 수정 불가능한 컬럼
READONLY_COLUMNS = ['id', 'created_at', 'updated_at', 'uploaded_at']





@router.get("/tables", response_model=List[str])
async def get_tables(
        current_user: models.AdminUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """데이터베이스의 테이블 목록을 반환합니다."""
    if current_user.permission not in ['admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )

    try:
        inspector = inspect(engine)
        all_tables = inspector.get_table_names()

        # 허용된 테이블만 반환
        allowed_tables = [table for table in all_tables if table in ALLOWED_TABLES]

        print(f"All tables: {all_tables}")  # 디버깅용
        print(f"Allowed tables: {allowed_tables}")  # 디버깅용

        return allowed_tables

    except Exception as e:
        print(f"Error getting tables: {e}")  # 디버깅용
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"테이블 목록 조회 중 오류 발생: {str(e)}"
        )


@router.get("/table/{table_name}")
async def get_table_data(
        table_name: str,
        current_user: models.AdminUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """특정 테이블의 데이터를 반환합니다."""
    if current_user.permission not in ['admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )

    if table_name not in ALLOWED_TABLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="접근이 허용되지 않은 테이블입니다."
        )

    try:
        # 테이블 메타데이터 가져오기
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]

        # 데이터 조회 (최대 1000개)
        result = db.execute(text(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 1000"))
        rows = []

        for row in result:
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                # datetime 객체를 문자열로 변환
                if isinstance(value, (datetime, date)):
                    value = value.isoformat()
                row_dict[column] = value
            rows.append(row_dict)

        return {
            "table": table_name,
            "columns": columns,
            "rows": rows
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터 조회 중 오류 발생: {str(e)}"
        )


@router.put("/table/{table_name}/update")
async def update_table_data(
        table_name: str,
        updates: Dict[str, Any],
        current_user: models.AdminUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """테이블 데이터를 업데이트합니다."""
    if current_user.permission != 'superadmin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="슈퍼관리자 권한이 필요합니다."
        )

    if table_name not in ALLOWED_TABLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="접근이 허용되지 않은 테이블입니다."
        )

    try:
        for update in updates['updates']:
            row_id = update['id']
            data = update['data']

            # SET 절 생성
            set_clauses = []
            params = {"id": row_id}

            for column, value in data.items():
                if column not in READONLY_COLUMNS:
                    set_clauses.append(f"{column} = :{column}")
                    params[column] = value

            if set_clauses:
                query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = :id"
                db.execute(text(query), params)

        db.commit()
        return {"message": f"{len(updates['updates'])}개 행이 업데이트되었습니다."}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"업데이트 중 오류 발생: {str(e)}"
        )


@router.delete("/table/{table_name}/delete")
async def delete_table_data(
        table_name: str,
        data: Dict[str, List[int]],
        current_user: models.AdminUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """테이블 데이터를 삭제합니다."""
    if current_user.permission != 'superadmin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="슈퍼관리자 권한이 필요합니다."
        )

    if table_name not in ALLOWED_TABLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="접근이 허용되지 않은 테이블입니다."
        )

    try:
        ids = data['ids']
        if ids:
            # IN 절을 위한 파라미터 생성
            placeholders = ', '.join([f':id{i}' for i in range(len(ids))])
            params = {f'id{i}': id_val for i, id_val in enumerate(ids)}

            query = f"DELETE FROM {table_name} WHERE id IN ({placeholders})"
            db.execute(text(query), params)
            db.commit()

        return {"message": f"{len(ids)}개 행이 삭제되었습니다."}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"삭제 중 오류 발생: {str(e)}"
        )


@router.post("/table/{table_name}/insert")
async def insert_table_data(
        table_name: str,
        data: Dict[str, Any],
        current_user: models.AdminUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """테이블에 새 데이터를 삽입합니다."""
    if current_user.permission != 'superadmin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="슈퍼관리자 권한이 필요합니다."
        )

    if table_name not in ALLOWED_TABLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="접근이 허용되지 않은 테이블입니다."
        )

    try:
        # 컬럼과 값 준비
        columns = []
        placeholders = []
        params = {}

        for column, value in data.items():
            if column not in READONLY_COLUMNS:
                columns.append(column)
                placeholders.append(f":{column}")
                params[column] = value

        if columns:
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            db.execute(text(query), params)
            db.commit()

        return {"message": "새 행이 추가되었습니다."}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"삽입 중 오류 발생: {str(e)}"
        )


@router.get("/test")
async def test_database_api():
    """데이터베이스 API 테스트"""
    return {"message": "Database API is working"}