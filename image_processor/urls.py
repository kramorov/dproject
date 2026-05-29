# image_processor/urls.py
from django.urls import path
from image_processor.views import ImageUploadView, ImageCropView, ImagePreviewView

urlpatterns = [
    path('upload/', ImageUploadView.as_view(), name='image-upload'),
    path('crop/', ImageCropView.as_view(), name='image-crop'),
    path('preview/', ImagePreviewView.as_view(), name='image-preview'),
]
