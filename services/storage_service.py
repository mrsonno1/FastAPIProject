# services/storage_service.py
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
import uuid

from core.config import settings


class StorageService:
    def __init__(self):
        self.bucket_name = None

        if settings.APP_ENV == 'production':
            # 프로덕션 환경: IAM Role을 사용하는 S3 클라이언트 초기화
            self.s3_client = boto3.client('s3', region_name=settings.AWS_S3_REGION)
            self.bucket_name = settings.AWS_S3_BUCKET_NAME
        else:
            # 로컬 환경: 기존 MinIO 클라이언트 초기화
            self.s3_client = boto3.client(
                's3',
                endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY,
            )
            self.bucket_name = settings.MINIO_BUCKET_NAME
            self.create_bucket_if_not_exists()  # MinIO에서만 버킷 생성 시도

    def create_bucket_if_not_exists(self):
        # 이 함수는 MinIO에서만 사용됩니다.
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            self.s3_client.create_bucket(Bucket=self.bucket_name)

    def upload_file(self, file: UploadFile) -> dict:
        file_extension = file.filename.split('.')[-1]
        object_name = f"uploads/{uuid.uuid4()}.{file_extension}"  # uploads/ 하위 경로에 저장

        extra_args = {'ContentType': file.content_type}
        if settings.APP_ENV == 'production':
            # S3에 업로드 시 공개 읽기 권한(ACL)을 부여해야 public URL로 접근 가능
            extra_args['ACL'] = 'public-read'

        try:
            self.s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                object_name,
                ExtraArgs=extra_args
            )

            # 환경에 따라 다른 Public URL 생성
            if settings.APP_ENV == 'production':
                public_url = f"https://{self.bucket_name}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{object_name}"
            else:  # local
                public_url = f"http://{settings.MINIO_ENDPOINT}/{self.bucket_name}/{object_name}"

            return {"object_name": object_name, "public_url": public_url}
        except ClientError as e:
            print(f"Error uploading file: {e}")
            return None

    def delete_file(self, object_name: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError as e:
            print(f"Error deleting file: {e}")
            return False


storage_service = StorageService()