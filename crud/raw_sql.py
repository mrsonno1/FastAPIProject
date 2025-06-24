# crud/raw_sql.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from typing import Dict


def execute_select_query(db: Session, query: str) -> Dict:
    """
    안전하게 SELECT 쿼리만 실행하고 결과를 반환합니다.
    """
    # SELECT 문이 아닌 다른 위험한 구문이 있는지 간단히 확인
    # (완벽한 방어는 아니지만, 기본적인 필터링 역할)
    upper_query = query.strip().upper()
    if not upper_query.startswith("SELECT"):
        raise HTTPException(status_code=400, detail="SELECT 쿼리만 실행할 수 있습니다.")

    # 세미콜론(;)을 이용한 다중 쿼리 실행 방지
    if ';' in upper_query and not upper_query.endswith(';'):
        raise HTTPException(status_code=400, detail="다중 쿼리는 허용되지 않습니다.")

    try:
        result_proxy = db.execute(text(query))

        # 컬럼 이름들을 가져옴
        columns = list(result_proxy.keys())

        # 결과 행들을 (컬럼명: 값) 형태의 딕셔너리 리스트로 변환
        rows = [dict(row) for row in result_proxy.mappings()]

        return {"columns": columns, "rows": rows, "row_count": len(rows)}
    except Exception as e:
        # 데이터베이스 에러 처리
        raise HTTPException(status_code=400, detail=f"쿼리 실행 중 오류가 발생했습니다: {str(e)}")


def execute_mutation_query(db: Session, query: str) -> Dict:
    """
    INSERT, UPDATE, DELETE 등의 데이터 변경 쿼리를 실행합니다.
    """
    upper_query = query.strip().upper()
    allowed_keywords = ("INSERT", "UPDATE", "DELETE")
    if not any(upper_query.startswith(keyword) for keyword in allowed_keywords):
        raise HTTPException(status_code=400, detail="INSERT, UPDATE, DELETE 쿼리만 실행할 수 있습니다.")

    try:
        # 트랜잭션 시작
        result_proxy = db.execute(text(query))
        row_count = result_proxy.rowcount
        db.commit()  # <-- 변경사항을 데이터베이스에 최종 반영합니다.

        # db.begin() 컨텍스트가 끝나면 자동으로 커밋됨
        return {"message": "쿼리가 성공적으로 실행되었습니다.", "row_count": row_count}
    except Exception as e:
        db.rollback()  # 오류 발생 시 롤백
        raise HTTPException(status_code=400, detail=f"쿼리 실행 중 오류가 발생했습니다: {str(e)}")