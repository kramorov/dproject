# storage_manager/storage_backends/cloudru.py
"""
Хранилище Cloud.ru Evolution Object Storage (S3-совместимое).

Два аккаунта:
    - Админ: полный доступ (upload, delete) — для админки
    - Читатель: только чтение (get_object, presigned URL) — для раздачи через фронт

Аутентификация: tenant_id:key_id в качестве Access Key.
"""
import boto3
from botocore.client import Config
from django.conf import settings
from .base import BaseStorage


class CloudRuStorage(BaseStorage):
    """
    Хранилище Cloud.ru Evolution Object Storage.
    """

    def __init__(self, location=None, base_url=None):
        super().__init__(location, base_url)

        self.bucket_name = settings.CLOUDRU_BUCKET_NAME
        self.endpoint_url = settings.CLOUDRU_ENDPOINT_URL
        self.region = settings.CLOUDRU_REGION

        # Админский клиент (полный доступ)
        admin_access = (
            f"{settings.CLOUDRU_ADMIN_TENANT_ID}:{settings.CLOUDRU_ADMIN_KEY_ID}"
        )
        self.s3_admin = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=admin_access,
            aws_secret_access_key=settings.CLOUDRU_ADMIN_KEY_SECRET,
            region_name=self.region,
            config=Config(signature_version='s3v4'),
        )

        # Читательский клиент (только чтение)
        reader_access = (
            f"{settings.CLOUDRU_READER_TENANT_ID}:{settings.CLOUDRU_READER_KEY_ID}"
        )
        self.s3_reader = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=reader_access,
            aws_secret_access_key=settings.CLOUDRU_READER_KEY_SECRET,
            region_name=self.region,
            config=Config(signature_version='s3v4'),
        )

    # ── Операции через админский аккаунт ──

    def _save(self, name, content):
        self.s3_admin.upload_fileobj(content, self.bucket_name, name)
        return name

    def delete(self, name):
        self.s3_admin.delete_object(Bucket=self.bucket_name, Key=name)

    # ── Операции через читательский аккаунт ──

    def _open(self, name, mode='rb'):
        from io import BytesIO
        response = self.s3_reader.get_object(
            Bucket=self.bucket_name, Key=name
        )
        return BytesIO(response['Body'].read())

    def exists(self, name):
        try:
            self.s3_reader.head_object(Bucket=self.bucket_name, Key=name)
            return True
        except Exception:
            return False

    def size(self, name):
        response = self.s3_reader.head_object(
            Bucket=self.bucket_name, Key=name
        )
        return response['ContentLength']

    def url(self, name):
        """Presigned URL через читательский аккаунт (1 час)."""
        return self.s3_reader.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': name},
            ExpiresIn=3600,
        )

    def get_available_name(self, name, max_length=None):
        return name
