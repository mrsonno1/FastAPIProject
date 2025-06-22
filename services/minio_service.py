# services/minio_service.py
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import UploadFile
import uuid

from core.config import settings


class MinioService:
    def __init__(self):
        # MinIO 클라이언트 초기화
        self.minio_client = boto3.client(
            's3',
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        # 버킷이 없으면 생성
        self.create_bucket_if_not_exists()

    def create_bucket_if_not_exists(self):
        try:
            self.minio_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            # 버킷이 없으면 404 에러가 발생함
            if e.response['Error']['Code'] == '404':
                self.minio_client.create_bucket(Bucket=self.bucket_name)
            else:
                raise

    def upload_file(self, file: UploadFile) -> dict:
        # 파일 이름 중복을 피하기 위해 UUID 사용
        file_extension = file.filename.split('.')[-1]
        object_name = f"{uuid.uuid4()}.{file_extension}"

        try:
            self.minio_client.upload_fileobj(
                file.file,
                self.bucket_name,
                object_name,
                ExtraArgs={'ContentType': file.content_type}
            )

            # 업로드된 파일의 공개 URL 생성
            public_url = (
                f"http://{settings.MINIO_ENDPOINT}/{self.bucket_name}/{object_name}"
            )

            return {"object_name": object_name, "public_url": public_url}
        except ClientError as e:
            # 업로드 실패 시 예외 처리
            print(f"Error uploading to MinIO: {e}")
            return None

    def delete_file(self, object_name: str) -> bool:
        """
        MinIO 버킷에서 특정 객체(파일)를 삭제합니다.
        :param object_name: 삭제할 파일의 이름 (UUID.jpg 등)
        :return: 성공 시 True, 실패 시 False
        """
        try:
            self.minio_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            print(f"Successfully deleted {object_name} from bucket {self.bucket_name}")
            return True
        except ClientError as e:
            print(f"Error deleting {object_name} from bucket {self.bucket_name}: {e}")
            return False


# 싱글턴처럼 사용할 수 있도록 인스턴스 생성
minio_service = MinioService()