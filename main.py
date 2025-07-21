# main.py
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from Enduser.routers import login as enduser_login_router
from Enduser.routers import custom_design as enduser_custom_design_router
from Enduser.routers import portfolio as enduser_portfolio_router
from Enduser.routers import cart as enduser_cart_router  # 추가
from Enduser.routers import sample as enduser_sample_router  # 추가
from Enduser.routers import brand as enduser_brand_router  # 추가
from Enduser.routers import released_product as enduser_released_product_router  # 추가
from Enduser.routers import share as enduser_share_router  # 추가
from Enduser.routers import language_setting as enduser_language_setting_router
from Enduser.routers import country as enduser_country_router
from Enduser import Email
from Manager.released_product.routers import released_product
from Manager.portfolio.routers import portfolio
from Manager.image.routers import upload
from Manager.custom_design.routers import custom_design
from Manager.country.routers import country
from Manager.color.routers import color
from Manager.brand.routers import brand
from Manager.admin.routers import auth, admin, database
from Manager.rank.routers import rank as rank
from Manager.progress_status.routers import progress_status
from db.database import engine, Base


from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# DB 테이블 생성 (프로덕션에서는 Alembic 같은 마이그레이션 도구 사용 권장)
Base.metadata.create_all(bind=engine)

# docs_url과 redoc_url을 /api 하위 경로로 지정합니다.
app = FastAPI(
    title="LensGrapick",
    version="0.6.0",
    description="LensGrapick API 설명입니다.<br>업데이트 : 2025 07 10 15 00",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 요청 크기 제한 설정 (50MB)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],
    # 이 미들웨어는 호스트 검증용이며, 실제 크기 제한은 서버 레벨에서 설정됩니다.
)


@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    """
    모든 API 응답에 대해 캐시를 비활성화하는 헤더를 추가합니다.
    브라우저가 항상 최신 데이터를 받도록 보장합니다.
    """
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# 허용할 출처(origin) 목록을 정의합니다.
# 개발 중에는 프론트엔드 개발 서버의 주소를 넣습니다.
# 예: React는 3000, Vue는 8080, Svelte는 5173 등
origins = [
    "http://localhost",
    "https://localhost",

    "http://localhost:3000",
    "https://localhost:3000",

    "http://localhost:8080",
    "https://localhost:8080",

    "http://52.79.185.227:3000",
    "https://52.79.185.227:3000",

    "http://10.10.100.85:3000",
    "https://10.10.100.85:3000",

    "http://10.10.101.39:3000",
    "https://10.10.101.39:3000",

    "http://10.10.100.197:3000",
    "https://10.10.100.197:3000",

    "https://admin.lensgrapick.com",
    "https://api.lensgrapick.com",
    "null"  # 로컬 파일(file://)에서의 요청을 허용하기 위해 추가

    # "https://your-frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 위에서 정의한 출처 목록
    #allow_origins=["*"],  # 위에서 정의한 출처 목록
    allow_credentials=True, # 쿠키를 포함한 요청을 허용할 것인지
    allow_methods=["*"],    # 모든 HTTP 메서드를 허용 (GET, POST, PUT, DELETE 등)
    allow_headers=["*"],    # 모든 HTTP 헤더를 허용
)

unity_router = APIRouter(prefix="/unity")
unity_router.include_router(enduser_login_router.router)
unity_router.include_router(enduser_custom_design_router.router)
unity_router.include_router(enduser_portfolio_router.router)
unity_router.include_router(enduser_cart_router.router)  # 추가
unity_router.include_router(enduser_sample_router.router)  # 추가
unity_router.include_router(enduser_brand_router.router)  # 추가
unity_router.include_router(enduser_released_product_router.router)  # 추가
unity_router.include_router(enduser_share_router.router)  # 추가
unity_router.include_router(enduser_language_setting_router.router)
unity_router.include_router(enduser_country_router.router)

unity_router.include_router(Email.router)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(upload.router)
api_router.include_router(color.router)
api_router.include_router(brand.router)
api_router.include_router(country.router)
api_router.include_router(custom_design.router)
api_router.include_router(portfolio.router)
api_router.include_router(released_product.router)
api_router.include_router(rank.router)
api_router.include_router(progress_status.router)


#database_router = APIRouter(prefix="/database")

api_router.include_router(database.router)

app.include_router(api_router)
app.include_router(unity_router)
#app.include_router(database_router)

# HTML 페이지 라우트 추가
@app.get("/admin/database", response_class=HTMLResponse)
async def database_manager():
    """데이터베이스 관리 페이지"""
    file_path = Path("templates/admin/database_manager.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/",include_in_schema=False)
def read_root():
    return {"message": "Welcome to the FastAPI Token Auth System"}