# image_processor/views.py
"""
API для интерактивной обрезки изображений.

POST /upload/   — загрузить оригинал, вернуть session_id + URL
POST /crop/     — применить crop-параметры, вернуть WebP-варианты
POST /preview/  — превью crop-области (без сохранения)
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, JSONParser
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from image_processor.models import ImageCropSession
from image_processor.services import process_crop_session, crop_and_pad
from PIL import Image
from io import BytesIO
import base64

DEFAULT_BG = '#F0F0F0'


def _checkerboard(size, cell=8):
    """Шахматный фон: светло-серый + белый, cell px на квадрат."""
    from PIL import Image
    w, h = size
    img = Image.new('RGB', (w, h), (255, 255, 255))
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            if (x // cell + y // cell) % 2 == 0:
                for dy in range(cell):
                    for dx in range(cell):
                        if x + dx < w and y + dy < h:
                            img.putpixel((x + dx, y + dy), (220, 220, 220))
    return img


@method_decorator(csrf_exempt, name='dispatch')
class ImageUploadView(APIView):
    """
    POST /api/image-processor/upload/
    Body: multipart/form-data, file=<image>

    Returns: { session_id, original_url, width, height }
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=400)

        session = ImageCropSession.objects.create()
        session.original_file.save(file.name, file, save=True)
        original_size = file.size

        content = session.original_file.read()
        img = Image.open(BytesIO(content))
        width, height = img.size

        return Response({
            'session_id': session.id,
            'original_url': session.original_file.url,
            'original_size': original_size,
            'width': width,
            'height': height,
        })


@method_decorator(csrf_exempt, name='dispatch')
class ImageCropView(APIView):
    """
    POST /api/image-processor/crop/
    Body: JSON
        {
            session_id: int,
            crop_x: float,
            crop_y: float,
            crop_size: float,
            background_color: '#FFFFFF' (optional)
        }

    Returns: { results: { sm: url, md: url, lg: url } }
    """
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        session_id = request.data.get('session_id')
        crop_x = request.data.get('crop_x')
        crop_y = request.data.get('crop_y')
        crop_size = request.data.get('crop_size')
        bg_color = request.data.get('background_color', DEFAULT_BG)
        remove_bg = request.data.get('remove_background', False)

        if session_id is None or crop_x is None or crop_y is None or crop_size is None:
            return Response({'error': 'Missing required fields'}, status=400)

        session = get_object_or_404(ImageCropSession, pk=session_id)
        session.crop_x = float(crop_x)
        session.crop_y = float(crop_y)
        session.crop_size = float(crop_size)
        session.background_color = bg_color
        session.remove_background = bool(remove_bg)
        session.save()

        try:
            sizes = process_crop_session(session)
        except RuntimeError as e:
            return Response({'error': str(e)}, status=400)

        response_data = {
            'session_id': session.id,
            'original_size': session.original_file.size,
            'cropped_size': sizes.get('cropped_size', 0),
            'results': {
                'sm': {'url': session.result_sm.url, 'size': sizes.get('sm', 0)},
                'md': {'url': session.result_md.url, 'size': sizes.get('md', 0)},
                'lg': {'url': session.result_lg.url, 'size': sizes.get('lg', 0)},
            },
        }
        if 'bg_removed_full_pct' in sizes:
            response_data['bg_removed_full_pct'] = sizes['bg_removed_full_pct']
            response_data['bg_removed_crop_pct'] = sizes['bg_removed_crop_pct']
        return Response(response_data)


@method_decorator(csrf_exempt, name='dispatch')
class ImagePreviewView(APIView):
    """
    POST /api/image-processor/preview/
    Body: JSON (те же поля что /crop/)
    Returns: { preview: base64-encoded JPEG }
    """
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        session_id = request.data.get('session_id')
        crop_x = request.data.get('crop_x')
        crop_y = request.data.get('crop_y')
        crop_size = request.data.get('crop_size')
        bg_color = request.data.get('background_color', DEFAULT_BG)
        remove_bg = request.data.get('remove_background', False)

        if session_id is None or crop_x is None or crop_y is None or crop_size is None:
            return Response({'error': 'Missing required fields'}, status=400)

        session = get_object_or_404(ImageCropSession, pk=session_id)

        content = session.original_file.read()
        img = Image.open(BytesIO(content))

        has_alpha = bool(remove_bg)
        if has_alpha:
            try:
                from image_processor.services import _remove_background
                img = _remove_background(img)
            except RuntimeError as e:
                return Response({'error': str(e)}, status=400)
        if not has_alpha:
            if img.mode == 'RGBA':
                from image_processor.services import hex_to_rgb
                bg = Image.new('RGB', img.size, hex_to_rgb(bg_color))
                bg.paste(img, (0, 0), img)
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')

        cropped = crop_and_pad(
            img, float(crop_x), float(crop_y), float(crop_size), bg_color,
            has_alpha=has_alpha,
        )

        # Уменьшить до md-размера для превью
        cropped.thumbnail((400, 400), Image.LANCZOS)

        # JPEG не поддерживает RGBA — шахматный фон для проверки прозрачности
        if cropped.mode == 'RGBA':
            bg = _checkerboard(cropped.size, 8)
            bg.paste(cropped, (0, 0), cropped)
            cropped = bg
        elif cropped.mode != 'RGB':
            cropped = cropped.convert('RGB')

        buf = BytesIO()
        cropped.save(buf, 'JPEG', quality=85)
        buf.seek(0)
        preview_b64 = base64.b64encode(buf.read()).decode()

        return Response({
            'preview': f'data:image/jpeg;base64,{preview_b64}',
        })