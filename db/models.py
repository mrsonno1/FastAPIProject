# db/models.py
from sqlalchemy import Column, Integer, String, TIMESTAMP, UniqueConstraint, DateTime, Text, Boolean
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
    email = Column(String(100), unique=True, nullable=True, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_login_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    brand_name = Column(String, unique=True, index=True, nullable=False)
    brand_image_url = Column(String)
    object_name = Column(String, nullable=True)
    rank = Column(Integer, nullable=False, index=True)

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    country_name = Column(String, unique=True, index=True, nullable=False)
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

class CustomDesign(Base):
    __tablename__ = "custom_designs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    item_name = Column(String(50), unique=True, nullable=False)
    status = Column(String(20), default="대기") # 기본값을 셋팅
    request_message = Column(Text, nullable=True)
    main_image_url = Column(String, nullable=True)

    design_line = Column(JSON, nullable=True)  # 라인
    design_base1 = Column(JSON, nullable=True)  # 바탕1
    design_base2 = Column(JSON, nullable=True)  # 바탕2
    design_pupil = Column(JSON, nullable=True)  # 동공

    graphic_diameter = Column(String(20), nullable=True)  # 그래픽직경
    optic_zone = Column(String(20), nullable=True)  # 옵틱존

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    item_name = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), default="대기") # 기본값을 셋팅
    color_name = Column(String(50), nullable=False)
    exposed_countries = Column(JSON, nullable=True)
    is_fixed_axis = Column(Boolean, default=False)  # 축고정
    request_message = Column(Text, nullable=True)
    main_image_url = Column(String, nullable=False)

    design_line = Column(JSON, nullable=True)  # 라인
    design_base1 = Column(JSON, nullable=True)  # 바탕1
    design_base2 = Column(JSON, nullable=True)  # 바탕2
    design_pupil = Column(JSON, nullable=True)  # 동공

    graphic_diameter = Column(String(20), nullable=True)  # 그래픽직경
    optic_zone = Column(String(20), nullable=True)  # 옵틱존

    views = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Releasedproduct(Base):
    __tablename__ = "releasedproducts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    design_name = Column(String(50), unique=True, nullable=False, index=True)
    color_name = Column(String(50), nullable=False)
    brand = Column(JSON, nullable=False)
    request_message = Column(Text, nullable=True)
    main_image_url = Column(String, nullable=False)

    color_line = Column(JSON, nullable=True)  # 라인
    color_base1 = Column(JSON, nullable=True)  # 바탕1
    color_base2 = Column(JSON, nullable=True)  # 바탕2
    color_pupil = Column(JSON, nullable=True)  # 동공

    graphic_diameter = Column(String(20), nullable=True)  # 그래픽직경
    optic_zone = Column(String(20), nullable=True)  # 옵틱존
    base_curve = Column(String(20), nullable=True)  # 베이스커브

    views = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Progressstatus(Base):
    __tablename__ = "progressstatus"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
