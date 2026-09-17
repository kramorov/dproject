# media_library/views/admin_ocr_tool.py
"""
Инструмент «Распознавание (OCR)» — файловый поток (без медиабиблиотеки).

POST /api/admin/media/ocr/recognize/  (multipart) — загрузить файл, распознать,
        вернуть превью (текст + таблицы) и result_id.
POST /api/admin/media/ocr/export/     (json)     — result_id + format (xlsx|docx),
        вернуть готовый файл как attachment.

Распознанный результат кешируется в локальном временном каталоге (JSON),
поэтому повторный OCR при экспорте не выполняется.
"""

import json
import logging
import os
import tempfile
import time
import uuid

from django.http import HttpResponse
from rest_framework import status
from rest_framework.parsers import JSONParser , MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from media_library.table_extractor import (
    TableExtractionError ,
    available_backends ,
    crop_image_bytes ,
    default_backend ,
    recognize_pages ,
    result_to_docx_bytes ,
    result_to_excel_bytes ,
)
from project_customers.permissions import SectionAccessPermission

logger = logging.getLogger(__name__)

_TMP_DIR = os.path.join(tempfile.gettempdir() , 'django_ocr_tool')
_TMP_TTL = 60 * 60  # 1 час
_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 МБ


def _tmp_dir() -> str :
    os.makedirs(_TMP_DIR , exist_ok=True)
    return _TMP_DIR


def _cleanup() -> None :
    try :
        now = time.time()
        for name in os.listdir(_tmp_dir()) :
            path = os.path.join(_tmp_dir() , name)
            if os.path.isfile(path) and now - os.path.getmtime(path) > _TMP_TTL :
                os.remove(path)
    except OSError :
        pass


def _json_default(obj) :
    """Fallback для numpy-скаляров в json.dump (защита от 500 на всём результате)."""
    try :
        import numpy as np
        if isinstance(obj , (np.integer ,)) :
            return int(obj)
        if isinstance(obj , (np.floating ,)) :
            return float(obj)
        if isinstance(obj , (np.bool_ ,)) :
            return bool(obj)
    except ImportError :
        pass
    raise TypeError(
        f'Object of type {obj.__class__.__name__} is not JSON serializable'
    )


def _save_result(result : dict) -> str :
    _cleanup()
    token = uuid.uuid4().hex
    path = os.path.join(_tmp_dir() , f'{token}.json')
    with open(path , 'w' , encoding='utf-8') as f :
        json.dump(result , f , ensure_ascii=False , default=_json_default)
    return token


def _load_result(token) -> dict | None :
    token = os.path.basename(str(token or ''))
    if not token or any(ch in token for ch in ('\\' , '/' , '.')) :
        return None
    path = os.path.join(_tmp_dir() , f'{token}.json')
    if not os.path.exists(path) :
        return None
    try :
        with open(path , 'r' , encoding='utf-8') as f :
            return json.load(f)
    except (OSError , json.JSONDecodeError) :
        return None


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


def _parse_region(data) :
    """Распарсить region_x/y/w/h в кортеж (x, y, w, h); None, если не заданы."""
    keys = ('region_x' , 'region_y' , 'region_w' , 'region_h')
    if any(data.get(k) in (None , '') for k in keys) :
        return None
    try :
        return tuple(int(data.get(k)) for k in keys)
    except (TypeError , ValueError) :
        return None


def _sanitize_filename(name : str) -> str :
    for ch in ('\\' , '/' , ':' , '*' , '?' , '"' , '<' , '>' , '|') :
        name = name.replace(ch , '_')
    return name.strip() or 'ocr'


def _file_to_pages(data : bytes , filename : str) -> list :
    """Изображение → [bytes]; PDF → список PNG по страницам."""
    name = (filename or '').lower()
    if name.endswith('.pdf') or data[:5] == b'%PDF-' :
        import fitz
        try :
            doc = fitz.open(stream=data , filetype='pdf')
            if doc.page_count == 0 :
                raise TableExtractionError('PDF пуст.')
            pages = []
            for page in doc :
                pix = page.get_pixmap(dpi=200)
                pages.append(pix.tobytes('png'))
            return pages
        except TableExtractionError :
            raise
        except Exception as e :
            raise TableExtractionError(f'Не удалось открыть PDF: {e}') from e
    return [data]


class MediaOcrRecognizeView(APIView) :
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'  # TODO: вернуть IsAdminUser
    parser_classes = [MultiPartParser]

    def post(self , request) :
        file = request.FILES.get('file')
        if not file :
            return Response({'error' : 'file is required'} , status=status.HTTP_400_BAD_REQUEST)

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

        if file.size > _MAX_UPLOAD_BYTES :
            return Response(
                {'error' : f'Файл больше {_MAX_UPLOAD_BYTES // (1024 * 1024)} МБ.'} ,
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE ,
            )

        raw = file.read()
        try :
            pages = _file_to_pages(raw , file.name)
            region = _parse_region(data)
            if region is not None and len(pages) == 1 :
                pages = [crop_image_bytes(pages[0] , *region)]
            result = recognize_pages(
                pages ,
                ocr_backend=ocr_backend ,
                ocr_kwargs=data.get('ocr_kwargs') or {} ,
                borderless_tables=_as_bool(data.get('borderless_tables') , False) ,
                implicit_rows=_as_bool(data.get('implicit_rows') , True) ,
                min_confidence=_as_int(data.get('min_confidence') , 50) ,
                max_workers=_as_int(data.get('max_workers') , 1) ,
                use_first_row_as_header=_as_bool(data.get('use_first_row_as_header') , True) ,
            )
        except TableExtractionError as e :
            return Response({'error' : str(e)} , status=status.HTTP_400_BAD_REQUEST)
        except Exception as e :
            logger.exception('OCR recognize failed')
            return Response({'error' : str(e)} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        result['filename'] = file.name
        result_id = _save_result(result)

        return Response({
            'result_id' : result_id ,
            'filename' : file.name ,
            'ocr_backend' : ocr_backend ,
            'page_count' : result.get('page_count') ,
            'count' : len(result.get('tables') or []) ,
            'text' : result.get('text') or '' ,
            'tables' : result.get('tables') or [] ,
            'pages' : result.get('pages') or [] ,
        })


class MediaOcrExportView(APIView) :
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'  # TODO: вернуть IsAdminUser
    parser_classes = [JSONParser]

    def post(self , request) :
        result = _load_result(request.data.get('result_id'))
        if result is None :
            return Response(
                {'error' : 'Результат не найден (истёк или неверный result_id).' } ,
                status=status.HTTP_404_NOT_FOUND ,
            )

        fmt = str(request.data.get('format' , 'xlsx')).strip().lower()
        try :
            if fmt in ('docx' , 'word') :
                content = result_to_docx_bytes(result)
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                ext = 'docx'
            elif fmt in ('xlsx' , 'excel') :
                content = result_to_excel_bytes(result)
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ext = 'xlsx'
            else :
                return Response(
                    {'error' : 'format должен быть "xlsx" или "docx".'} ,
                    status=status.HTTP_400_BAD_REQUEST ,
                )
        except Exception as e :
            logger.exception('OCR export failed')
            return Response({'error' : str(e)} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        base = _sanitize_filename(os.path.splitext(result.get('filename') or 'ocr')[0])
        filename = f'{base}.{ext}'
        response = HttpResponse(content , content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
