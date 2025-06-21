# db/models.py
from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from .database import Base

class AdminUser(Base):
    __tablename__ = "관리자계정"

    # Python 변수명 = Column("DB 컬럼명", 타입, 제약조건)
    id = Column("index", Integer, primary_key=True)
    permission = Column("권한", String(50), nullable=False)
    # '계정코드' 필드 추가
    account_code = Column("계정코드", String(10), unique=True, nullable=True)  # nullable=True로 설정
    username = Column("아이디", String(50), unique=True, nullable=False, index=True)
    hashed_password = Column("비밀번호", String(100), nullable=False)
    company_name = Column("소속사업자명", String(20))
    contact_name = Column("담당자명", String(100))
    contact_phone = Column("담당자연락처", String(50))
    email = Column("이메일", String(100), unique=True, nullable=False, index=True)
    created_at = Column("생성시간", TIMESTAMP(timezone=True), server_default=func.now())
    # '접속시간'은 로그인 시마다 업데이트해야 하므로, Python 코드에서 처리합니다.
    # DB 기본값으로 CURRENT_TIMESTAMP를 사용하면 생성 시에만 적용됩니다.
    last_login_at = Column("접속시간", TIMESTAMP(timezone=True), server_default=func.now())