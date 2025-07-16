from fastapi import FastAPI, APIRouter
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr, BaseModel  # BaseModel을 가져옵니다.
from fastapi import HTTPException
from email.mime.text import MIMEText
import smtplib
import ssl

router = APIRouter(prefix="/mail", tags=["email"])


# Cafe24 메일 서버 설정
SMTP_SERVER = "smtp.cafe24.com"
SMTP_PORT = 587
EMAIL = "lensgrapick@dkmv.co.kr"



@router.post("/send-email")
async def send_email(to_email: str, subject: str, body: str):
    # 이메일 메시지 생성
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = to_email

    try:
        # SSL/TLS 컨텍스트 설정
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2  # TLS 1.2 이상 강제
        context.set_ciphers("DEFAULT@SECLEVEL=1")  # 호환성 강화를 위해 낮은 보안 레벨

        # SMTP 서버 연결
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=30)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
            server.set_debuglevel(1)  # 디버깅 활성화
            server.starttls(context=context)

        server.login("lensgrapick", "lgp00100")
        server.send_message(msg)
        server.quit()
        return {"message": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
