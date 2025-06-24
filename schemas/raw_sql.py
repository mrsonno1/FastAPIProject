# schemas/raw_sql.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# SQL 쿼리를 입력받기 위한 스키마
class RawSQLQuery(BaseModel):
    query: str

# SELECT 쿼리의 결과를 반환하기 위한 스키마
class QueryResult(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int

# INSERT, UPDATE, DELETE 쿼리의 결과를 반환하기 위한 스키마
class ExecuteResult(BaseModel):
    message: str
    row_count: int