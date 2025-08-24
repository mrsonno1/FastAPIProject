# db/models.py
from sqlalchemy import Column, Integer, String, TIMESTAMP, UniqueConstraint, DateTime, Text, Boolean, Date, ForeignKey, \
    Index
from sqlalchemy.sql import func
from .database import Base
from sqlalchemy.types import JSON

class AdminUser(Base):
    __tablename__ = "account"

    # Python 변수명 = Column("DB 컬럼명", 타입, 제약조건)
    id = Column(Integer, primary_key=True)
    permission = Column(String(50), nullable=False)
    account_code = Column(String(10), unique=True, nullable=True)  # nullable=True로 설정
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(100), nullable=False)
    company_name = Column(String(20), nullable=False)
    contact_name = Column(String(100))
    contact_phone = Column(String(50))
    email = Column(String(100), nullable=True, index=True)  # unique=True 제거 - 중복 이메일 허용
    language_preference = Column(String(10), nullable=False, default='ko')  # 언어 설정 (ko, en)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_login_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    is_deleted = Column(Boolean, default=False, nullable=False)  # 소프트 삭제를 위한 필드

class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    brand_name = Column(String, unique=True, index=True, nullable=False)
    brand_image_url = Column(String)
    thumbnail_url = Column(String, nullable=True)  # 썸네일 URL
    object_name = Column(String, nullable=True)
    rank = Column(Integer, nullable=False, index=True)

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    country_name = Column(String, unique=True, index=True, nullable=False)
    country_name_en = Column(String, index=True, nullable=True)  # 영문 이름 추가
    rank = Column(Integer, nullable=False, index=True)

class Image(Base):
    __tablename__ = "images"
    __table_args__ = (
        UniqueConstraint('category', 'display_name', name='_category_display_name_uc'),
    )
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False, index=True)
    display_name = Column(String, index=True, nullable=False)
    object_name = Column(String, index=True)
    public_url = Column(String, unique=True)
    thumbnail_url = Column(String, nullable=True)  # 썸네일 URL
    exposed_users = Column(String, nullable=True)  # 노출 사용자 ID 목록 (예: "1,2,3,4,5")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    uploaded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Color(Base):
    __tablename__ = "colors"

    id = Column(Integer, primary_key=True, index=True)
    color_name = Column(String, index=True, nullable=True)  # nullable=True로 변경, unique 제거 (빈 문자열 중복 허용)
    color_values = Column(String(100), nullable=False)
    monochrome_type = Column(String(10), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

class CustomDesign(Base):
    __tablename__ = "custom_designs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(20), nullable=False)  # 프로덕션 DB에 맞게 varchar(20)로 변경
    item_name = Column(String(50), nullable=True)  # unique=True 제거, 복합 unique는 __table_args__에서 처리
    status = Column(String(20), default="0") # 기본값을 셋팅
    request_message = Column(Text, nullable=True)
    main_image_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)  # 썸네일 URL

    design_line_image_id = Column(String(6), nullable=True)  # 라인 테이블의 id (FK키)
    design_line_color_id = Column(String(6), nullable=True)  # 컬러 테이블 id (FK키)
    design_base1_image_id = Column(String(6), nullable=True)  # 바탕1 테이블의 id (FK키)
    design_base1_color_id = Column(String(6), nullable=True)  # 컬러 테이블 id (FK키)
    design_base2_image_id = Column(String(6), nullable=True)  # 바탕2 테이블의 id (FK키)
    design_base2_color_id = Column(String(6), nullable=True)  # 컬러 테이블 id (FK키)
    design_pupil_image_id = Column(String(6), nullable=True)  # 동공 테이블의 id (FK키)
    design_pupil_color_id = Column(String(6), nullable=True)  # 컬러 테이블 id (FK키)

    line_transparency = Column(String(6), nullable=True)  # 라인 투명도
    base1_transparency = Column(String(6), nullable=True)  # 라인 투명도
    base2_transparency = Column(String(6), nullable=True)  # 라인 투명도
    pupil_transparency = Column(String(6), nullable=True)  # 라인 투명도

    # 새로 추가되는 size 필드들
    line_size = Column(String(6), nullable=True)  # 라인 크기
    base1_size = Column(String(6), nullable=True)  # 바탕1 크기
    base2_size = Column(String(6), nullable=True)  # 바탕2 크기
    pupil_size = Column(String(6), nullable=True)  # 동공 크기

    graphic_diameter = Column(String(20), nullable=True)  # 그래픽직경
    optic_zone = Column(String(20), nullable=True)  # 옵틱존
    dia = Column(String(20), nullable=True, default="14")  # DIA
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'item_name', name='custom_designs_user_item_unique'),
    )


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    design_name = Column(String(100), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    deleted_at = Column(DateTime, nullable=True)

    color_name = Column(String(100), nullable=True)
    exposed_countries = Column(String(100), nullable=True)  # 노출국가 (국가 id , 기준 ex-> 1,2,3,4)
    is_fixed_axis = Column(String(1), nullable=False, default='N')  # 축고정 (Y/N)
    main_image_url = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=True)  # 썸네일 URL

    design_line_image_id = Column(String(6), nullable=True)  # 라인 테이블의 id (FK키)
    design_line_color_id = Column(String(6), nullable=True)  # 컬러 테이블 id (FK키)

    design_base1_image_id = Column(String(6), nullable=True)  # 바탕1 테이블의 id (FK키)
    design_base1_color_id = Column(String(6), nullable=True)  # 컬러 테이블 id (FK키)

    design_base2_image_id = Column(String(6), nullable=True)  # 바탕2 테이블의 id (FK키)
    design_base2_color_id = Column(String(6), nullable=True)  # 컬러 테이블 id (FK키)

    design_pupil_image_id = Column(String(6), nullable=True)  # 동공 테이블의 id (FK키)
    design_pupil_color_id = Column(String(6), nullable=True)  # 컬러 테이블 id (FK키)

    graphic_diameter = Column(String(100), nullable=True)  # 그래픽직경
    optic_zone = Column(String(100), nullable=True)  # 옵틱존
    dia = Column(String(20), nullable=True, default="14")  # DIA

    views = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Releasedproduct(Base):
    __tablename__ = "releasedproducts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    design_name = Column(String(50), nullable=False, index=True)
    color_name = Column(String(50), nullable=True)
    brand_id = Column(Integer, nullable=False)
    request_message = Column(Text, nullable=True)
    main_image_url = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=True)  # 썸네일 URL

    color_line_color_id = Column(String(6), nullable=True)  # 컬러 테이블 id (FK키)
    color_base1_color_id = Column(String(6), nullable=True)  # 컬러 테이블 id (FK키)
    color_base2_color_id = Column(String(6), nullable=True)  # 컬러 테이블 id (FK키)
    color_pupil_color_id = Column(String(6), nullable=True)  # 컬러 테이블 id (FK키)

    graphic_diameter = Column(String(20), nullable=True)  # 그래픽직경
    optic_zone = Column(String(20), nullable=True)  # 옵틱존
    dia = Column(String(20), nullable=True, default="14")  # DIA
    base_curve = Column(String(20), nullable=True)  # 베이스커브

    views = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# --- [새로운 DailyView 모델 추가] ---
class DailyView(Base):
    __tablename__ = "daily_views"

    id = Column(Integer, primary_key=True, index=True)
    view_date = Column(Date, nullable=False, index=True)  # 조회 날짜 (YYYY-MM-DD)

    # 어떤 종류의 콘텐츠인지 구분 (released_product 또는 portfolio)
    content_type = Column(String(50), nullable=False)

    # 해당 콘텐츠의 ID
    content_id = Column(Integer, nullable=False, index=True)

    # 해당 날짜의 조회수
    view_count = Column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint('view_date', 'content_type', 'content_id', name='_daily_view_uc'),
    )


class Progressstatus(Base):
    __tablename__ = "progressstatus"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    custom_design_id = Column(Integer, ForeignKey("custom_designs.id"), nullable=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    status = Column(String(1), nullable=False, default='0')  # 0: 대기, 1: 진행중, 2: 지연, 3: 배송완료
    notes = Column(Text, nullable=True)

    # 새로 추가되는 필드들
    client_name = Column(String(100), nullable=True)  # 받는사람
    number = Column(String(50), nullable=True)  # 연락처
    address = Column(Text, nullable=True)  # 주소
    status_note = Column(Text, nullable=True)  # 진행현황 노트
    request_date = Column(DateTime(timezone=True), server_default=func.now())  # 요청일
    expected_shipping_date = Column(Date, nullable=True)  # 예상 배송일
    changelog = Column(Text, nullable=True)  # 변경 이력

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)  # AdminUser의 username
    item_name = Column(String(100), nullable=False)
    main_image_url = Column(String, nullable=True)
    category = Column(String(20), nullable=False)  # '커스텀디자인' 또는 '포트폴리오'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'item_name', 'category', name='_user_item_category_uc'),
    )


class Share(Base):
    __tablename__ = "shares"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(String(50), unique=True, nullable=False, index=True)  # 고유 이미지 ID
    user_id = Column(String(50), nullable=False)  # AdminUser의 username
    item_name = Column(String(100), nullable=False)
    category = Column(String(20), nullable=False)  # '커스텀디자인' 또는 '포트폴리오'
    image_url = Column(String, nullable=False)  # S3 업로드된 이미지 URL
    object_name = Column(String, nullable=True)  # S3 object name
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'item_name', 'category', name='_user_share_item_uc'),
    )

class RealtimeUser(Base):
    __tablename__ = "realtime_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)  # AdminUser의 username
    content_type = Column(String(20), nullable=False)  # 'portfolio' 또는 'released_product'
    content_name = Column(String(100), nullable=False, index=True)  # design_name
    entered_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'content_type', 'content_name', name='_user_content_uc'),
        Index('idx_entered_at', 'entered_at'),  # 만료된 레코드 삭제를 위한 인덱스
    )