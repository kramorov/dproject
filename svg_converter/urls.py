# svg_converter/urls.py
from django.urls import path
from svg_converter.views import SvgUploadView, SvgPreviewView, SvgConvertView, PdfToDocxView

urlpatterns = [
    path('upload/', SvgUploadView.as_view(), name='svg-upload'),
    path('preview/', SvgPreviewView.as_view(), name='svg-preview'),
    path('convert/', SvgConvertView.as_view(), name='svg-convert'),
    path('to-docx/', PdfToDocxView.as_view(), name='pdf-to-docx'),
    path('to-docx/<str:task_id>/', PdfToDocxView.as_view(), name='pdf-to-docx-status'),
]
