from fastapi import APIRouter, HTTPException, Body, File, UploadFile, Form
from pydantic import BaseModel, EmailStr
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64
from services.storage_service import storage_service

router = APIRouter(prefix="/mail", tags=["email"])
email_router = APIRouter(prefix="/email", tags=["email"])


# API 요청 본문을 위한 Pydantic 모델
class EmailSchema(BaseModel):
    to_email: EmailStr  # 이메일 형식 자동 검증
    subject: str
    body: str


class EmailBase64Schema(BaseModel):
    to_email: EmailStr  # 수신자 이메일
    base64_image: str  # base64 인코딩된 이미지 데이터
    subject: str = "이미지 전송"  # 기본 제목


class ImageUrlSchema(BaseModel):
    base64_image: str  # base64 인코딩된 이미지 데이터


@router.post("/sendbase64")
def send_email_with_base64_image(email_data: EmailBase64Schema = Body(...)):
    """Base64 이미지를 S3에 업로드하고 이메일로 전송합니다."""
    
    try:
        # 1. Base64 이미지 데이터를 디코딩
        try:
            # base64 문자열에서 데이터 URI 스킴 제거 (있는 경우)
            if ',' in email_data.base64_image:
                image_data = email_data.base64_image.split(',')[1]
            else:
                image_data = email_data.base64_image
            
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 base64 이미지 데이터입니다: {e}")
        
        # 2. 이미지를 S3로 업로드
        upload_result = storage_service.upload_base64_file(
            file_data=image_bytes,
            filename="email_image.png",
            content_type="image/png"
        )
        
        if not upload_result:
            raise HTTPException(status_code=500, detail="이미지 업로드에 실패했습니다.")
        
        image_url = upload_result["public_url"]
        
        # 3. 이메일 전송
        SMTP_SERVER = "smtp.cafe24.com"
        SMTP_PORT = 587
        SMTP_USER = "lensgrapick@dkmv.co.kr"
        SMTP_PASSWORD = "lgp00100"
        
        # 이메일 메시지 생성
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = email_data.to_email
        msg['Subject'] = email_data.subject
        
        # HTML 템플릿에 이미지 URL 포함
        html_content = f"""
<html>
                <body style="background-color: #f0f2f5; margin: 0; padding: 0;">
                    <table width="100%" border="0" cellspacing="0" cellpadding="0" align="center">
                        <tr>
                            <td align="center">
                                <table width="800" height="820" border="0" cellspacing="0" cellpadding="0" align="center">
                                    <tr>
                                        <td background="https://lensgrapick-bucket.s3.ap-northeast-2.amazonaws.com/uploads/634398a4-1b03-4bb4-9fd4-abdf7dacacaf.png" width="800" height="820" valign="middle" align="center">
                                            <table width="500" height="500" border="0" cellspacing="0" cellpadding="0" align="center">
                                                <tr>
                                                    <td align="center">
                                                        <img src="{image_url}" width="500" height="500" style="display: block;" >
                                                    </td>
                                                </tr>
                                            </table>
                                            <table width="500" border="0" cellspacing="0" cellpadding="0" align="center" style="position: relative; top: -30px;">
                                                <tr>
                                                    <td align="center" style="color: #1a73e8; font-size: 12px; font-weight: bold;">
                                                        © Lensgrapick. 이미지 무단 사용 금지
                                                    </td>
                                                </tr>
                                                <tr>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
            </html>
        """
        
        msg.attach(MIMEText(html_content, 'html'))
        
        # SSL 컨텍스트 설정
        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # 이메일 전송
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, email_data.to_email, msg.as_string())
        except Exception as e:
            # 다른 방법으로 재시도
            try:
                with smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context) as server:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(SMTP_USER, email_data.to_email, msg.as_string())
            except:
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(SMTP_USER, email_data.to_email, msg.as_string())
        
        return {
            "message": "이메일이 성공적으로 전송되었습니다.",
            "image_url": image_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예기치 않은 오류가 발생했습니다: {e}")


@router.post("/imageurl")
def upload_base64_image(image_data: ImageUrlSchema = Body(...)):
    """Base64 이미지를 S3에 업로드하고 URL을 반환합니다."""
    
    try:
        # Base64 이미지 데이터를 디코딩
        try:
            # base64 문자열에서 데이터 URI 스킴 제거 (있는 경우)
            if ',' in image_data.base64_image:
                decoded_image = image_data.base64_image.split(',')[1]
            else:
                decoded_image = image_data.base64_image
            
            image_bytes = base64.b64decode(decoded_image)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 base64 이미지 데이터입니다: {e}")
        
        # 이미지를 S3로 업로드
        upload_result = storage_service.upload_base64_file(
            file_data=image_bytes,
            filename="qr_image.png",
            content_type="image/png"
        )
        
        if not upload_result:
            raise HTTPException(status_code=500, detail="이미지 업로드에 실패했습니다.")
        
        return {
            "image_url": upload_result["public_url"],
            "object_name": upload_result["object_name"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예기치 않은 오류가 발생했습니다: {e}")

