# main.py
from fastapi import FastAPI
from routers import auth, admin
from db.database import engine, Base

# DB 테이블 생성 (프로덕션에서는 Alembic 같은 마이그레이션 도구 사용 권장)
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)
#admin 라우터 포함
app.include_router(admin.router)
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI Token Auth System"}