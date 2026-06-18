# svg_converter/views.py
"""
API для конвертации изображений в SVG.

POST /upload/   — загрузить оригинал, вернуть session_id + размеры
POST /preview/  — превью области выделения (JPEG base64)
POST /convert/  — векторизация + обрезка → SVG
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, JSONParser
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from io import BytesIO
import base64
import logging

from svg_converter.models import SvgConversionSession
from svg_converter.services import process_svg_conversion, open_image_or_pdf
from svg_converter.pdf_to_docx import pdf_to_docx as convert_pdf_to_docx

logger = logging.getLogger(__name__)

# In-memory хранилище задач конвертации
_tasks = {}


@method_decorator(csrf_exempt, name='dispatch')
class SvgUploadView(APIView):
    """
    POST /api/svg-converter/upload/
    Body: multipart/form-data, file=<image|pdf>
    Returns: { session_id, filename, width, height }
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=400)

        session = SvgConversionSession(
            original_filename=file.name,
        )
        session.original_file.save(file.name, file, save=True)
        session.save(update_fields=['original_filename'])

        # Определяем размеры
        session.original_file.seek(0)
        content = session.original_file.read()
        try:
            img = open_image_or_pdf(content, file.name)
            session.original_width, session.original_height = img.size
        except Exception:
            session.original_width, session.original_height = 0, 0
        finally:
            session.save(update_fields=['original_width', 'original_height'])

        return Response({
            'session_id': session.id,
            'filename': file.name,
            'width': session.original_width,
            'height': session.original_height,
        })


@method_decorator(csrf_exempt, name='dispatch')
class SvgPreviewView(APIView):
    """
    POST /api/svg-converter/preview/
    Body: { session_id, region_x?, region_y?, region_w?, region_h? }
    Returns: { preview: "data:image/jpeg;base64,..." }

    Возвращает обрезанный оригинал (растр) для предпросмотра выделенной области.
    """
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({'error': 'session_id required'}, status=400)

        session = get_object_or_404(SvgConversionSession, id=session_id)

        session.original_file.seek(0)
        content = session.original_file.read()
        img = open_image_or_pdf(content, session.original_filename or '')

        # Обрезка по области, если задана
        rx = request.data.get('region_x')
        ry = request.data.get('region_y')
        rw = request.data.get('region_w')
        rh = request.data.get('region_h')

        if all(v is not None and v != '' for v in [rx, ry, rw, rh]):
            rx, ry, rw, rh = int(rx), int(ry), int(rw), int(rh)
            try:
                rx, ry, rw, rh = int(rx), int(ry), int(rw), int(rh)
                if rw > 0 and rh > 0:
                    img = img.crop((rx, ry, rx + rw, ry + rh))
            except (ValueError, TypeError):
                return Response({'error': 'region_* must be integers'}, status=400)

        # Кодируем в JPEG base64
        buf = BytesIO()
        img.save(buf, format='JPEG', quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()

        return Response({
            'preview': f'data:image/jpeg;base64,{b64}',
            'width': img.size[0],
            'height': img.size[1],
        })


@method_decorator(csrf_exempt, name='dispatch')
class SvgConvertView(APIView):
    """
    POST /api/svg-converter/convert/
    Body: { session_id, color_mode?, threshold?, region_*? }
    Returns: { svg: "<svg>...</svg>", filename }

    Выполняет полный pipeline: предобработка → vtracer → обрезка → SVG.
    """
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({'error': 'session_id required'}, status=400)

        session = get_object_or_404(SvgConversionSession, id=session_id)

        # Применяем параметры из запроса
        if 'color_mode' in request.data:
            session.color_mode = request.data['color_mode']
        if 'threshold' in request.data:
            session.threshold = int(request.data['threshold'])
        if 'region_x' in request.data:
            session.region_x = float(request.data['region_x'])
        if 'region_y' in request.data:
            session.region_y = float(request.data['region_y'])
        if 'region_w' in request.data:
            session.region_w = float(request.data['region_w'])
        if 'region_h' in request.data:
            session.region_h = float(request.data['region_h'])

        try:
            svg = process_svg_conversion(session)
            session.svg_content = svg
            session.save()

            return Response({
                'svg': svg,
                'filename': session.original_filename.rsplit('.', 1)[0] + '.svg',
            })
        except Exception as e:
            logger.error(f'SVG convert failed: {e}', exc_info=True)
            return Response({'error': f'{type(e).__name__}: {e}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class PdfToDocxView(APIView):
    """
    POST /api/svg-converter/to-docx/
    Body: multipart/form-data, file=<pdf>
    Returns: SSE-поток с прогрессом, финальный event — download_url
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=400)

        if not file.name.lower().endswith('.pdf'):
            return Response({'error': 'Only PDF files supported'}, status=400)

        pdf_bytes = file.read()
        filename = file.name.rsplit('.', 1)[0]
        strip_images = request.GET.get('strip_images') == '1'
        preview_only = request.GET.get('preview') == '1'

        if preview_only:
            from svg_converter.pdf_to_docx import extract_text_blocks
            pages = extract_text_blocks(pdf_bytes)
            return Response({
                'pages': [{'n': i + 1, 'blocks': page} for i, page in enumerate(pages)],
                'total_pages': len(pages),
            })

        import uuid, threading, time
        task_id = uuid.uuid4().hex[:12]
        _tasks[task_id] = {'status': 'processing', 'message': 'Начало...', '_started': time.time()}

        def _run():
            # Перехватываем логи pdf2docx → сообщения на фронт
            import queue as _q
            log_queue = _q.Queue()

            class _Handler(logging.Handler):
                def emit(self, record):
                    log_queue.put(record.getMessage())

            handler = _Handler()
            handler.setLevel(logging.INFO)
            old_levels = {}
            for log_name in ('pdf2docx', 'converter'):
                lg = logging.getLogger(log_name)
                old_levels[log_name] = lg.level
                lg.addHandler(handler)
                lg.setLevel(logging.INFO)

            import time as _time
            _flush_stop = False

            def _flush_loop():
                while not _flush_stop:
                    try:
                        msg = log_queue.get(timeout=0.5)
                        if any(skip in msg for skip in ('DEBUG:', 'pixmap', 'stream')):
                            continue
                        _tasks[task_id]['message'] = msg
                    except _q.Empty:
                        pass

            flush_thread = threading.Thread(target=_flush_loop, daemon=True)
            flush_thread.start()

            try:
                docx_bytes = convert_pdf_to_docx(pdf_bytes, strip_images=strip_images)
                docx_name = f'pdf_to_docx/{uuid.uuid4().hex}.docx'
                from django.core.files.base import ContentFile
                session = SvgConversionSession.objects.create(
                    original_filename=f'{filename}.docx'
                )
                session.original_file.save(docx_name, ContentFile(docx_bytes), save=True)
                _tasks[task_id] = {
                    'status': 'done',
                    'message': 'Готово',
                    'download_url': session.original_file.url,
                    'filename': f'{filename}.docx',
                }
            except Exception as e:
                _tasks[task_id] = {'status': 'error', 'message': str(e)}
            finally:
                _flush_stop = True
                flush_thread.join(timeout=2)
                for log_name in ('pdf2docx', 'converter'):
                    lg = logging.getLogger(log_name)
                    lg.removeHandler(handler)
                    lg.setLevel(old_levels[log_name])

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return Response({'task_id': task_id})

    def get(self, request, task_id=None):
        """GET /api/svg-converter/to-docx/{task_id}/ — статус задачи."""
        if not task_id:
            return Response({'error': 'task_id required'}, status=400)
        task = _tasks.get(task_id)
        if not task:
            return Response({'error': 'Task not found'}, status=404)
        # Добавляем elapsed, если задача ещё в процессе
        if task.get('status') == 'processing':
            import time
            started = task.get('_started', 0)
            if started:
                task['elapsed'] = int(time.time() - started)
        return Response(task)

