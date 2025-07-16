from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, EmailStr
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

router = APIRouter(prefix="/mail", tags=["email"])


# API 요청 본문을 위한 Pydantic 모델
class EmailSchema(BaseModel):
    to_email: EmailStr  # 이메일 형식 자동 검증
    subject: str
    body: str


@router.post("/send-email")
def send_email_endpoint(email: EmailSchema = Body(...)):
    """제공된 상세 정보를 사용하여 이메일을 전송합니다."""

    try:
        # SMTP Configuration - 추후 보안을 위해 환경변수나 별도 설정 파일로 옮기는 것을 권장합니다.
        SMTP_SERVER = "smtp.cafe24.com"
        SMTP_PORT = 587
        SMTP_USER = "lensgrapick@dkmv.co.kr"
        SMTP_PASSWORD = "lgp00100"

        # 이메일 메시지 생성 (MIMEMultipart 사용)
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = email.to_email
        msg['Subject'] = email.subject
        msg.attach(MIMEText(email.body, 'plain'))

        # SSL 컨텍스트 설정을 더 유연하게 수정
        context = ssl.create_default_context()
        # 보안 수준을 낮추고 더 많은 암호화 방식을 허용
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        # 인증서 검증을 비활성화 (테스트 환경에서만 사용)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        try:
            # 방법 1: STARTTLS를 사용한 연결
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, email.to_email, msg.as_string())

        except Exception as starttls_error:
            print(f"STARTTLS 연결 실패: {starttls_error}")

            # 방법 2: SSL 직접 연결 (포트 465 사용)
            try:
                with smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context) as server:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(SMTP_USER, email.to_email, msg.as_string())

            except Exception as ssl_error:
                print(f"SSL 직접 연결 실패: {ssl_error}")

                # 방법 3: 암호화 없이 연결 (보안상 권장하지 않음)
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(SMTP_USER, email.to_email, msg.as_string())

        return {"message": "Email sent successfully"}

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=500, detail="SMTP 인증에 실패했습니다. 아이디 또는 비밀번호를 확인하세요.")
    except smtplib.SMTPException as e:
        raise HTTPException(status_code=500, detail=f"이메일 전송 중 SMTP 오류가 발생했습니다: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예기치 않은 오류가 발생했습니다: {e}")