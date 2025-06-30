# main.py
from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, admin, upload, color, raw_sql, brand, country, custom_design
from db.database import engine, Base

# DB 테이블 생성 (프로덕션에서는 Alembic 같은 마이그레이션 도구 사용 권장)
Base.metadata.create_all(bind=engine)

# docs_url과 redoc_url을 /api 하위 경로로 지정합니다.
app = FastAPI(
    title="LensGrapick",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
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


api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(upload.router)
api_router.include_router(color.router)
api_router.include_router(raw_sql.router)
api_router.include_router(brand.router)
api_router.include_router(country.router)
app.include_router(custom_design.router)


# 앱에 api_router를 포함시킵니다.
app.include_router(api_router)




@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI Token Auth System"}