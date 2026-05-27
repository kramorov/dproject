# storage_manager/storage_backends/cloudru.py
"""
Хранилище Cloud.ru Evolution Object Storage (S3-совместимое).

Аутентификация: tenant_id:key_id в качестве Access Key.
"""
import boto3
from botocore.client import Config
from django.conf import settings
from .base import BaseStorage


class CloudRuStorage(BaseStorage):

    def __init__(self, location=None, base_url=None):
        super().__init__(location, base_url)
        self.bucket_name = settings.CLOUDRU_BUCKET_NAME
        self.endpoint_url = settings.CLOUDRU_ENDPOINT_URL
        self.region = settings.CLOUDRU_REGION
        admin_access = f"{settings.CLOUDRU_ADMIN_TENANT_ID}:{settings.CLOUDRU_ADMIN_KEY_ID}"
        self.s3_admin = boto3.client('s3', endpoint_url=self.endpoint_url,
            aws_access_key_id=admin_access,
            aws_secret_access_key=settings.CLOUDRU_ADMIN_KEY_SECRET,
            region_name=self.region, config=Config(signature_version='s3v4'))
        reader_access = f"{settings.CLOUDRU_READER_TENANT_ID}:{settings.CLOUDRU_READER_KEY_ID}"
        self.s3_reader = boto3.client('s3', endpoint_url=self.endpoint_url,
            aws_access_key_id=reader_access,
            aws_secret_access_key=settings.CLOUDRU_READER_KEY_SECRET,
            region_name=self.region, config=Config(signature_version='s3v4'))

    def _normalize(self, name):
        return name.replace('\\', '/')

    def _resolve_name(self, name):
        """Возвращает реальный ключ в S3 (с прямыми или обратными слешами)."""
        name = self._normalize(name)
        try:
            self.s3_reader.head_object(Bucket=self.bucket_name, Key=name)
            return name
        except Exception:
            alt = name.replace('/', '\\')
            if alt != name:
                try:
                    self.s3_reader.head_object(Bucket=self.bucket_name, Key=alt)
                    return alt
                except Exception:
                    pass
            return name  # fallback — вернём нормализованный

    def _save(self, name, content):
        name = self._normalize(name)
        self.s3_admin.upload_fileobj(content, self.bucket_name, name)
        return name

    def delete(self, name):
        name = self._normalize(name)
        self.s3_admin.delete_object(Bucket=self.bucket_name, Key=name)

    def _open(self, name, mode='rb'):
        from io import BytesIO
        name = self._resolve_name(name)
        response = self.s3_reader.get_object(Bucket=self.bucket_name, Key=name)
        return BytesIO(response['Body'].read())

    def exists(self, name):
        resolved = self._resolve_name(name)
        try:
            self.s3_reader.head_object(Bucket=self.bucket_name, Key=resolved)
            return True
        except Exception:
            return False

    def size(self, name):
        name = self._resolve_name(name)
        response = self.s3_reader.head_object(Bucket=self.bucket_name, Key=name)
        return response['ContentLength']

    def url(self, name):
        name = self._resolve_name(name)
        return self.s3_reader.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': name},
            ExpiresIn=3600)

    def get_available_name(self, name, max_length=None):
        return name