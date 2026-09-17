# media_library/views/admin_table_extract.py
"""
POST /api/admin/media/<pk>/extract-tables/

Распознавание таблиц на изображении медиаэлемента через img2table.

Тело запроса (всё опционально):
    ocr               — имя OCR-бэкенда (tesseract | rapidocr | surya | paddle | easyocr | doctr);
                        по умолчанию из настроек MEDIA_TABLE_OCR_BACKEND или tesseract
    ocr_kwargs        — dict параметров OCR (например {"lang": "eng"})
    borderless_tables — искать таблицы без линий (bool)
    implicit_rows     — достраивать неявные строки (bool)
    min_confidence    — минимальная уверенность детекции (int, 0-100)
    max_workers       — число потоков OCR (int)
    format            — "json" (по умолчанию) или "excel"

Ответ (format=json): {"source": {...}, "count": N, "tables": [{...}]}
Ответ (format=excel): файл .xlsx как attachment.
"""

import logging

from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from media_library.models import MediaLibraryItem
from media_library.table_extractor import (
    TableExtractionError ,
    available_backends ,
    default_backend ,
    extract_tables ,
    tables_to_excel_bytes ,
    tables_to_preview ,
)
from project_customers.permissions import SectionAccessPermission

logger = logging.getLogger(__name__)


def _as_bool(value , default=False) -> bool :
    if value is None :
        return default
    if isinstance(value , bool) :
        return value
    if isinstance(value , (int , float)) :
        return bool(value)
    return str(value).strip().lower() in ('true' , '1' , 'yes' , 'on')


def _as_int(value , default) -> int :
    try :
        return int(value)
    except (TypeError , ValueError) :
        return default


def _sanitize_filename(name : str) -> str :
    """Убрать символы, недопустимые в имени файла."""
    for ch in ('\\' , '/' , ':' , '*' , '?' , '"' , '<' , '>' , '|') :
        name = name.replace(ch , '_')
    return name.strip() or 'media'


class MediaAdminTableExtractView(APIView) :
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'  # TODO: вернуть IsAdminUser

    def post(self , request , pk) :
        item = MediaLibraryItem.objects.filter(pk=pk).first()
        if item is None :
            return Response({'error' : 'Not found'} , status=status.HTTP_404_NOT_FOUND)

        if not item.is_image() :
            return Response(
                {'error' : 'Элемент не является изображением'} ,
                status=status.HTTP_400_BAD_REQUEST ,
            )

        data = request.data or {}
        ocr_backend = str(data.get('ocr') or default_backend()).strip().lower()
        if ocr_backend not in available_backends() :
            return Response(
                {
                    'error' : f'Неизвестный OCR-бэкенд "{ocr_backend}".' ,
                    'available' : available_backends() ,
                } ,
                status=status.HTTP_400_BAD_REQUEST ,
            )

        try :
            tables = extract_tables(
                item ,
                ocr_backend=ocr_backend ,
                ocr_kwargs=data.get('ocr_kwargs') or {} ,
                borderless_tables=_as_bool(data.get('borderless_tables') , False) ,
                implicit_rows=_as_bool(data.get('implicit_rows') , True) ,
                min_confidence=_as_int(data.get('min_confidence') , 50) ,
                max_workers=_as_int(data.get('max_workers') , 1) ,
            )
        except TableExtractionError as e :
            return Response({'error' : str(e)} , status=status.HTTP_400_BAD_REQUEST)
        except Exception as e :
            logger.exception(f'Ошибка распознавания таблиц для media pk={pk}')
            return Response(
                {'error' : str(e)} ,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR ,
            )

        output_format = str(data.get('format' , 'json')).strip().lower()

        if output_format == 'excel' :
            try :
                excel_bytes = tables_to_excel_bytes(tables)
            except TableExtractionError as e :
                return Response({'error' : str(e)} , status=status.HTTP_400_BAD_REQUEST)

            base = _sanitize_filename(item.code or item.name or str(item.pk))
            filename = f'{base}_tables.xlsx'
            response = HttpResponse(
                excel_bytes ,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ,
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        preview = tables_to_preview(tables)
        return Response({
            'source' : {
                'id' : item.pk ,
                'name' : item.name ,
                'code' : item.code ,
            } ,
            'ocr_backend' : ocr_backend ,
            'count' : len(preview) ,
            'tables' : preview ,
        })
