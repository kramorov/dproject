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
from io import BytesIO

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


def _save_result(result : dict , owner : str) -> str :
    _cleanup()
    token = uuid.uuid4().hex
    result['_owner'] = owner
    path = os.path.join(_tmp_dir() , f'{token}.json')
    with open(path , 'w' , encoding='utf-8') as f :
        json.dump(result , f , ensure_ascii=False , default=_json_default)
    return token


def _load_result(token , owner : str) -> dict | None :
    """Загрузить результат только для владельца (token не является секретом)."""
    token = os.path.basename(str(token or ''))
    if not token or any(ch in token for ch in ('\\' , '/' , '.')) :
        return None
    path = os.path.join(_tmp_dir() , f'{token}.json')
    if not os.path.exists(path) :
        return None
    try :
        with open(path , 'r' , encoding='utf-8') as f :
            result = json.load(f)
    except (OSError , json.JSONDecodeError) :
        return None
    if result.get('_owner') != owner :
        return None
    return result


def _owner_key(request) -> str :
    """Стабильный ключ владельца: pk пользователя, иначе ключ сессии."""
    user = getattr(request , 'user' , None)
    if user is not None and getattr(user , 'is_authenticated' , False) :
        return f'user:{user.pk}'
    session = getattr(request , 'session' , None)
    session_key = getattr(session , 'session_key' , '') or ''
    return f'session:{session_key or "unknown"}'


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


def _attachment_response(content , content_type : str , filename : str) -> HttpResponse :
    """Ответ-файл с корректным Content-Disposition (ASCII + RFC 5987 для UTF-8).

    ``filename`` — полное имя с расширением; может содержать кириллицу.
    """
    from urllib.parse import quote
    filename = _sanitize_filename(str(filename or '')) or 'file'
    ascii_name = filename.encode('ascii' , 'ignore').decode('ascii').strip() or 'file'
    response = HttpResponse(content , content_type=content_type)
    response['Content-Disposition'] = (
        f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{quote(filename)}'
    )
    return response


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


def _attach_checkboxes(result : dict , pages : list) -> None :
    """Дополнить результат распознаванием чек-боксов по каждой странице.

    Добавляет в ``result`` ключи:
        form_fields — список по страницам ({'page', 'checkboxes', 'groups', 'selected'}),
        checkboxes  — плоский список всех чек-боксов,
        selected    — подписи отмеченных чек-боксов.
    """
    from media_library.form_extractor import extract_form_fields

    result['form_fields'] = []
    result['checkboxes'] = []
    result['selected'] = []

    for i , page_bytes in enumerate(pages) :
        try :
            fields = extract_form_fields(page_bytes)
        except Exception as e :
            logger.warning('Распознавание чек-боксов (стр. %d): %s' , (i + 1) , e)
            fields = {'checkboxes' : [] , 'selected' : [] , 'groups' : []}

        fields['page'] = i + 1
        if result.get('pages') and i < len(result['pages']) :
            page = result['pages'][i]
            page['checkboxes'] = fields.get('checkboxes') or []
            page['groups'] = fields.get('groups') or []

        result['form_fields'].append(fields)
        for cb in (fields.get('checkboxes') or []) :
            cb['page'] = i + 1
            result['checkboxes'].append(cb)
        result['selected'].extend(fields.get('selected') or [])


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
            if _as_bool(data.get('detect_checkboxes') , False) :
                _attach_checkboxes(result , pages)
        except TableExtractionError as e :
            return Response({'error' : str(e)} , status=status.HTTP_400_BAD_REQUEST)
        except Exception as e :
            logger.exception('OCR recognize failed')
            return Response({'error' : str(e)} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        result['filename'] = file.name
        result_id = _save_result(result , _owner_key(request))

        return Response({
            'result_id' : result_id ,
            'filename' : file.name ,
            'ocr_backend' : ocr_backend ,
            'page_count' : result.get('page_count') ,
            'count' : len(result.get('tables') or []) ,
            'text' : result.get('text') or '' ,
            'tables' : result.get('tables') or [] ,
            'pages' : result.get('pages') or [] ,
            'checkboxes' : result.get('checkboxes') or [] ,
            'selected' : result.get('selected') or [] ,
            'form_fields' : result.get('form_fields') or [] ,
        })


class MediaOcrExportView(APIView) :
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'  # TODO: вернуть IsAdminUser
    parser_classes = [JSONParser]

    def post(self , request) :
        result = _load_result(request.data.get('result_id') , _owner_key(request))
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
        return _attachment_response(content , content_type , f'{base}.{ext}')


class MediaOcrCheckboxLabelView(APIView) :
    """Распознать текст внутри области «чек-бокс + подпись» (ручная разметка).

    POST /api/admin/media/ocr/checkbox-label/  (multipart)
        file — изображение, x/y/w/h — область чек-бокса вместе с подписью.
    Ответ: {"label": "..."}
    """
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'  # TODO: вернуть IsAdminUser
    parser_classes = [MultiPartParser]

    def post(self , request) :
        file = request.FILES.get('file')
        if not file :
            return Response({'error' : 'file is required'} , status=status.HTTP_400_BAD_REQUEST)

        data = request.data or {}
        try :
            region = (
                int(data.get('x')) , int(data.get('y')) ,
                int(data.get('w')) , int(data.get('h')) ,
            )
        except (TypeError , ValueError) :
            return Response(
                {'error' : 'x/y/w/h должны быть целыми числами.'} ,
                status=status.HTTP_400_BAD_REQUEST ,
            )

        if region[2] <= 0 or region[3] <= 0 :
            return Response(
                {'error' : 'Пустая область.'} ,
                status=status.HTTP_400_BAD_REQUEST ,
            )

        raw = file.read()
        try :
            from media_library.form_extractor import ocr_text_in_region
            label = ocr_text_in_region(raw , region)
        except Exception as e :
            logger.exception('OCR checkbox label failed')
            return Response({'error' : str(e)} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'label' : label})


class MediaOcrRegionView(APIView) :
    """Разбор произвольной области изображения (для ручной разметки ОЛ).

    POST /api/admin/media/ocr/region/  (multipart)
        file — изображение, x/y/w/h — область в пикселях исходника.
        kind — 'text' (OCR текста) или 'value' (автоопределение значения:
               чек-боксы / таблица / текст). По умолчанию 'text'.
    """
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'  # TODO: вернуть IsAdminUser
    parser_classes = [MultiPartParser]

    def post(self , request) :
        file = request.FILES.get('file')
        if not file :
            return Response({'error' : 'file is required'} , status=status.HTTP_400_BAD_REQUEST)

        data = request.data or {}
        kind = str(data.get('kind' , 'text')).strip().lower()
        try :
            region = (
                int(data.get('x')) , int(data.get('y')) ,
                int(data.get('w')) , int(data.get('h')) ,
            )
        except (TypeError , ValueError) :
            return Response(
                {'error' : 'x/y/w/h должны быть целыми числами.'} ,
                status=status.HTTP_400_BAD_REQUEST ,
            )

        if region[2] <= 0 or region[3] <= 0 :
            return Response(
                {'error' : 'Пустая область.'} ,
                status=status.HTTP_400_BAD_REQUEST ,
            )

        raw = file.read()
        try :
            from media_library.form_extractor import (
                analyze_region , extract_fv_table , ocr_text_in_area ,
            )
            if kind == 'value' :
                result = analyze_region(raw , region)
            elif kind == 'fvtable' :
                result = {'rows' : extract_fv_table(raw , region)}
            else :
                result = {'text' : ocr_text_in_area(raw , region)}
        except Exception as e :
            logger.exception('OCR region failed')
            return Response({'error' : str(e)} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(result)


class MediaOcrStructureExportView(APIView) :
    """Экспорт размеченной структуры ОЛ (JSON-дерева) в Word/Excel.

    POST /api/admin/media/ocr/export-structure/  (json)
        {structure: {...}, format: 'xlsx'|'docx'}
    Ответ: файл как attachment.
    """
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'  # TODO: вернуть IsAdminUser
    parser_classes = [JSONParser]

    def post(self , request) :
        structure = request.data.get('structure') or {}
        fmt = str(request.data.get('format' , 'xlsx')).strip().lower()
        try :
            from media_library.form_export import structure_to_docx , structure_to_xlsx
            if fmt in ('docx' , 'word') :
                content = structure_to_docx(structure)
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                ext = 'docx'
            else :
                content = structure_to_xlsx(structure)
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ext = 'xlsx'
        except Exception as e :
            logger.exception('Structure export failed')
            return Response({'error' : str(e)} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        base = _sanitize_filename(
            os.path.splitext(str(request.data.get('filename') or 'структура'))[0]
        )
        return _attachment_response(content , content_type , f'{base}.{ext}')


class MediaOcrRegionsView(APIView) :
    """Пакетный разбор областей: файл один раз + список регионов.

    POST /api/admin/media/ocr/regions/  (multipart)
        file — изображение (для PDF — PNG одной страницы),
        regions — JSON: [{"id", "kind", "x", "y", "w", "h"}, ...]
            kind: 'text' | 'fvtable' | 'grid'
        use_first_row_as_header / borderless_tables — опции для kind='grid'
    Ответ: {"results": [{"id", ...payload|error}, ...]} — порядок не гарантируется,
    сопоставление по id.
    """
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'  # TODO: вернуть IsAdminUser
    parser_classes = [MultiPartParser]

    _MAX_REGIONS = 200

    def post(self , request) :
        file = request.FILES.get('file')
        if not file :
            return Response({'error' : 'file is required'} , status=status.HTTP_400_BAD_REQUEST)

        data = request.data or {}
        try :
            regions = json.loads(data.get('regions') or '[]')
        except (TypeError , json.JSONDecodeError) :
            return Response(
                {'error' : 'regions должен быть JSON-массивом.'} ,
                status=status.HTTP_400_BAD_REQUEST ,
            )
        if not isinstance(regions , list) :
            return Response(
                {'error' : 'regions должен быть JSON-массивом.'} ,
                status=status.HTTP_400_BAD_REQUEST ,
            )
        regions = regions[:self._MAX_REGIONS]

        use_header = _as_bool(data.get('use_first_row_as_header') , True)
        borderless = _as_bool(data.get('borderless_tables') , False)

        raw = file.read()
        from media_library.form_extractor import extract_fv_table , ocr_text_in_area
        from media_library.table_extractor import (
            crop_image_bytes , extract_tables , table_to_dict ,
        )

        results = []
        for item in regions :
            if not isinstance(item , dict) :
                results.append({'id' : None , 'error' : 'неверный формат региона'})
                continue
            rid = item.get('id')
            kind = str(item.get('kind') or 'text').strip().lower()
            try :
                region = (
                    int(item.get('x')) , int(item.get('y')) ,
                    int(item.get('w')) , int(item.get('h')) ,
                )
            except (TypeError , ValueError) :
                results.append({'id' : rid , 'error' : 'x/y/w/h должны быть целыми числами'})
                continue
            if region[2] <= 0 or region[3] <= 0 :
                results.append({'id' : rid , 'error' : 'Пустая область.'})
                continue
            try :
                if kind == 'fvtable' :
                    results.append({'id' : rid , 'rows' : extract_fv_table(raw , region)})
                elif kind == 'grid' :
                    crop = crop_image_bytes(raw , *region)
                    tables = extract_tables(
                        crop , ocr_backend=default_backend() ,
                        borderless_tables=borderless ,
                    )
                    if tables :
                        d = table_to_dict(
                            tables[0] , 0 , use_first_row_as_header=use_header
                        )
                        results.append({'id' : rid , 'columns' : d['columns'] , 'rows' : d['rows']})
                    else :
                        results.append({'id' : rid , 'columns' : [] , 'rows' : []})
                else :
                    results.append({'id' : rid , 'text' : ocr_text_in_area(raw , region)})
            except Exception as e :
                logger.warning('OCR batch region %s failed: %s' , rid , e)
                results.append({'id' : rid , 'error' : str(e)})

        return Response({'results' : results})


class MediaOcrPagesView(APIView) :
    """Страницы документа как изображения (для разметки PDF).

    POST /api/admin/media/ocr/pages/  (multipart, file) →
        {token, page_count, pages: [{w, h}, ...], filename}
    GET  /api/admin/media/ocr/pages/<token>/<n>/ → PNG страницы n (1-based).

    Изображение → одна страница; PDF → рендер страниц (200 dpi, PNG).
    Страницы живут в том же временном кэше, что и результаты распознавания.
    """
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'  # TODO: вернуть IsAdminUser
    parser_classes = [MultiPartParser]

    def post(self , request) :
        file = request.FILES.get('file')
        if not file :
            return Response({'error' : 'file is required'} , status=status.HTTP_400_BAD_REQUEST)
        if file.size > _MAX_UPLOAD_BYTES :
            return Response(
                {'error' : f'Файл больше {_MAX_UPLOAD_BYTES // (1024 * 1024)} МБ.'} ,
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE ,
            )

        raw = file.read()
        try :
            pages = _file_to_page_images(raw , file.name)
        except TableExtractionError as e :
            return Response({'error' : str(e)} , status=status.HTTP_400_BAD_REQUEST)
        except Exception as e :
            logger.exception('PDF pages failed')
            return Response({'error' : str(e)} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        _cleanup()
        token = uuid.uuid4().hex
        for i , (png , _ , _) in enumerate(pages , start=1) :
            with open(os.path.join(_tmp_dir() , f'{token}_{i}.png') , 'wb') as f :
                f.write(png)
        meta = {
            'owner' : _owner_key(request) ,
            'filename' : file.name ,
            'page_count' : len(pages) ,
            'pages' : [{'w' : w , 'h' : h} for _ , w , h in pages] ,
        }
        with open(os.path.join(_tmp_dir() , f'{token}.meta.json') , 'w' , encoding='utf-8') as f :
            json.dump(meta , f , ensure_ascii=False)

        return Response({
            'token' : token ,
            'filename' : file.name ,
            'page_count' : len(pages) ,
            'pages' : meta['pages'] ,
        })

    def get(self , request , token , page) :
        token = os.path.basename(str(token or ''))
        if not token or any(ch in token for ch in ('\\' , '/' , '.')) :
            return HttpResponse(status=404)
        try :
            page = int(page)
        except (TypeError , ValueError) :
            return HttpResponse(status=404)

        meta_path = os.path.join(_tmp_dir() , f'{token}.meta.json')
        if not os.path.exists(meta_path) :
            return HttpResponse(status=404)
        try :
            with open(meta_path , 'r' , encoding='utf-8') as f :
                meta = json.load(f)
        except (OSError , json.JSONDecodeError) :
            return HttpResponse(status=404)

        if meta.get('owner') != _owner_key(request) :
            return HttpResponse(status=404)
        if page < 1 or page > int(meta.get('page_count' , 0)) :
            return HttpResponse(status=404)

        path = os.path.join(_tmp_dir() , f'{token}_{page}.png')
        if not os.path.exists(path) :
            return HttpResponse(status=404)
        with open(path , 'rb') as f :
            png = f.read()
        return HttpResponse(png , content_type='image/png')


def _file_to_page_images(data : bytes , filename : str) -> list :
    """Файл → список (png_bytes, width, height). PDF → страницы (200 dpi)."""
    name = (filename or '').lower()
    if name.endswith('.pdf') or data[:5] == b'%PDF-' :
        import fitz
        doc = fitz.open(stream=data , filetype='pdf')
        if doc.page_count == 0 :
            raise TableExtractionError('PDF пуст.')
        pages = []
        for page in doc :
            pix = page.get_pixmap(dpi=200)
            pages.append((pix.tobytes('png') , pix.width , pix.height))
        return pages

    from PIL import Image
    img = Image.open(BytesIO(data))
    w , h = img.size
    buf = BytesIO()
    img.convert('RGB').save(buf , 'PNG')
    return [(buf.getvalue() , w , h)]
