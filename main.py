# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, admin, upload, color, raw_sql, brand, country
from db.database import engine, Base

# DB 테이블 생성 (프로덕션에서는 Alembic 같은 마이그레이션 도구 사용 권장)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LensGrapick")


# 허용할 출처(origin) 목록을 정의합니다.
# 개발 중에는 프론트엔드 개발 서버의 주소를 넣습니다.
# 예: React는 3000, Vue는 8080, Svelte는 5173 등
origins = [
    "http://localhost",
    "http://localhost:3000", # React 개발 서버
    "http://localhost:8080", # Vue 개발 서버
    "https://52.79.185.227",
    "http://52.79.185.227",
    "http://10.10.100.85:3000",
    "null"  # 로컬 파일(file://)에서의 요청을 허용하기 위해 추가
    # 여기에 실제 배포될 프론트엔드 도메인을 추가해야 합니다.
    # "https://your-frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 위에서 정의한 출처 목록
    allow_credentials=True, # 쿠키를 포함한 요청을 허용할 것인지
    allow_methods=["*"],    # 모든 HTTP 메서드를 허용 (GET, POST, PUT, DELETE 등)
    allow_headers=["*"],    # 모든 HTTP 헤더를 허용
)



app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(upload.router) # upload 라우터 등록
app.include_router(color.router)
app.include_router(raw_sql.router)
app.include_router(brand.router)
app.include_router(country.router)
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI Token Auth System"}