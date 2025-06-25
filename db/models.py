# db/models.py
from sqlalchemy import Column, Integer, String, TIMESTAMP, UniqueConstraint
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
    company_name = Column("소속사업자명", String(20), nullable=False)
    contact_name = Column("담당자명", String(100))
    contact_phone = Column("담당자연락처", String(50))
    email = Column("이메일", String(100), unique=True, nullable=True, index=True)
    created_at = Column("생성시간", TIMESTAMP(timezone=True), server_default=func.now())
    # '접속시간'은 로그인 시마다 업데이트해야 하므로, Python 코드에서 처리합니다.
    # DB 기본값으로 CURRENT_TIMESTAMP를 사용하면 생성 시에만 적용됩니다.
    last_login_at = Column("접속시간", TIMESTAMP(timezone=True), server_default=func.now())

class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    brand_name = Column(String, unique=True, index=True, nullable=False)
    brand_image_url = Column(String)
    object_name = Column(String, nullable=True)
    # 순위를 나타내는 정수형 컬럼. 값이 작을수록 순위가 높음.
    rank = Column(Integer, nullable=False, index=True)

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    country_name = Column(String, unique=True, index=True, nullable=False)
    # 순위를 나타내는 정수형 컬럼. 값이 작을수록 순위가 높음.
    rank = Column(Integer, nullable=False, index=True)

class Image(Base):
    __tablename__ = "images"
    __table_args__ = (
        UniqueConstraint('category', 'display_name', name='_category_display_name_uc'),
    )
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False, index=True)
    # 사용자가 지정하는 파일 이름 (예: '내 고양이 사진')
    display_name = Column(String, index=True, nullable=False)
    # S3/MinIO에 저장된 객체 이름 (예: uuid.jpg)
    object_name = Column(String, index=True)
    # 외부에서 접근 가능한 전체 URL
    public_url = Column(String, unique=True)
    uploaded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Color(Base):
    __tablename__ = "colors"

    id = Column(Integer, primary_key=True, index=True)
    color_name = Column(String, unique=True, index=True, nullable=False)
    color_values = Column(String(100), nullable=False)
    monochrome_type = Column(String(10), nullable=False)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
