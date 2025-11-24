# # storage_manager/storage_backends/yandex_cloud.py
# import boto3
# from botocore.client import Config
# from .base import BaseStorage
#
#
# class YandexCloudStorage(BaseStorage) :
#     """
#     Хранилище для Yandex Cloud Object Storage
#     """
#
#     def __init__(self , location=None , base_url=None) :
#         super().__init__(location , base_url)
#
#         from django.conf import settings
#
#         self.bucket_name = getattr(settings , 'YC_BUCKET_NAME' , 'your-bucket')
#         self.access_key = getattr(settings , 'YC_ACCESS_KEY' , '')
#         self.secret_key = getattr(settings , 'YC_SECRET_KEY' , '')
#         self.endpoint_url = getattr(settings , 'YC_ENDPOINT_URL' , 'https://storage.yandexcloud.net')
#         self.region = getattr(settings , 'YC_REGION' , 'ru-central1')
#
#         self.s3_client = boto3.client(
#             's3' ,
#             endpoint_url=self.endpoint_url ,
#             aws_access_key_id=self.access_key ,
#             aws_secret_access_key=self.secret_key ,
#             region_name=self.region ,
#             config=Config(signature_version='s3v4')
#         )
#
#     def _save(self , name , content) :
#         self.s3_client.upload_fileobj(
#             content ,
#             self.bucket_name ,
#             name ,
#             ExtraArgs={'ACL' : 'private'}
#         )
#         return name
#
#     def _open(self , name , mode='rb') :
#         from io import BytesIO
#         response = self.s3_client.get_object(Bucket=self.bucket_name , Key=name)
#         return BytesIO(response['Body'].read())
#
#     def delete(self , name) :
#         self.s3_client.delete_object(Bucket=self.bucket_name , Key=name)
#
#     def exists(self , name) :
#         try :
#             self.s3_client.head_object(Bucket=self.bucket_name , Key=name)
#             return True
#         except :
#             return False
#
#     def size(self , name) :
#         response = self.s3_client.head_object(Bucket=self.bucket_name , Key=name)
#         return response['ContentLength']
#
#     def url(self , name) :
#         # Генерируем presigned URL для доступа к файлу
#         return self.s3_client.generate_presigned_url(
#             'get_object' ,
#             Params={'Bucket' : self.bucket_name , 'Key' : name} ,
#             ExpiresIn=3600  # 1 час
#         )
#
#     def get_available_name(self , name , max_length=None) :
#         # В S3 имена уникальны в рамках бакета, поэтому просто возвращаем имя
#         return name