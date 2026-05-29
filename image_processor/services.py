# image_processor/services.py
"""
Генерация WebP-вариантов из crop-параметров.

Pipeline:
    1. Открыть оригинал (Pillow)
    2. [Опционально] Убрать фон нейросетью (rembg)
    3. Вырезать crop-область (crop_x, crop_y, crop_size)
    4. Добить фоном (background_color) — если рамка выходит за границы
    5. Сгенерировать WebP: sm(150), md(400), lg(800)
"""
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile


WEBP_SIZES = {
    'sm': 150,
    'md': 400,
    'lg': 800,
}
WEBP_QUALITY = 80


def _remove_background(img: Image.Image) -> Image.Image:
    """
    Убрать фон нейросетью rembg (U2Net).
    При первой загрузке качает ~170 MB модель.

    pip install rembg onnxruntime
    """
    try:
        from rembg import remove
    except ImportError:
        raise RuntimeError(
            'rembg not installed. Run: pip install rembg onnxruntime'
        )
    except BaseException as e:
        raise RuntimeError(
            f'rembg: ошибка загрузки ({e}).\n'
            'Проверьте onnxruntime: pip install onnxruntime\n'
            'Модель: %USERPROFILE%\\.u2net'
        )
    from io import BytesIO

    buf = BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    try:
        output = remove(buf.read())
    except SystemExit:
        raise RuntimeError(
            'rembg: не удалось загрузить модель U2Net.\n'
            'Проверьте интернет и права доступа к %USERPROFILE%\\.u2net'
        )
    except Exception as e:
        raise RuntimeError(f'rembg error: {e}')
    return Image.open(BytesIO(output)).convert('RGBA')


def hex_to_rgb(hex_color: str) -> tuple:
    """'#FFFFFF' | '#FFF' | 'FFFFFF' → (255, 255, 255)."""
    h = hex_color.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def crop_and_pad(img: Image.Image, crop_x: float, crop_y: float,
                crop_size: float, bg_hex: str, has_alpha: bool = False) -> Image.Image:
    """
    Вырезать квадратную область из img, добить фоном.

    has_alpha=True: canvas RGBA (прозрачный там, где нет img).
    has_alpha=False: canvas RGB с bg_hex.
    """
    size = int(crop_size)
    bg_rgb = hex_to_rgb(bg_hex)

    # Холст: прозрачный при has_alpha, иначе bgColor
    if has_alpha:
        canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    else:
        canvas = Image.new('RGB', (size, size), bg_rgb)

    # Вычисляем область img, попадающую в crop-рамку
    img_w, img_h = img.size
    crop_x_int = int(crop_x)
    crop_y_int = int(crop_y)

    # Область img, которая войдёт в canvas
    src_x1 = max(0, crop_x_int)
    src_y1 = max(0, crop_y_int)
    src_x2 = min(img_w, crop_x_int + size)
    src_y2 = min(img_h, crop_y_int + size)

    # Позиция на canvas, куда вставить фрагмент img
    dst_x1 = max(0, -crop_x_int)
    dst_y1 = max(0, -crop_y_int)

    if src_x2 > src_x1 and src_y2 > src_y1:
        fragment = img.crop((src_x1, src_y1, src_x2, src_y2))
        if has_alpha and fragment.mode == 'RGBA':
            # Прозрачность сохраняется: клеим RGBA на RGBA-холст
            canvas.paste(fragment, (dst_x1, dst_y1), fragment)
        elif has_alpha:
            canvas.paste(fragment, (dst_x1, dst_y1))
        else:
            if fragment.mode == 'RGBA':
                bg = Image.new('RGB', fragment.size, bg_rgb)
                bg.paste(fragment, (0, 0), fragment)
                fragment = bg
            elif fragment.mode != 'RGB':
                fragment = fragment.convert('RGB')
            canvas.paste(fragment, (dst_x1, dst_y1))

    return canvas


def generate_webp_variants(image: Image.Image) -> dict:
    """
    Сгенерировать WebP-варианты: sm, md, lg.
    RGBA → lossless WebP (прозрачность).

    Returns: {'sm': BytesIO, 'md': BytesIO, 'lg': BytesIO}
    """
    variants = {}
    for suffix, target_size in WEBP_SIZES.items():
        variant = image.copy()
        variant.thumbnail((target_size, target_size), Image.LANCZOS)
        buf = BytesIO()
        if variant.mode not in ('RGB', 'RGBA'):
            variant = variant.convert('RGB')
        variant.save(buf, 'WEBP', quality=WEBP_QUALITY)
        buf.seek(0)
        variants[suffix] = buf
    return variants


def process_crop_session(session) -> dict:
    """
    Основной pipeline для ImageCropSession.
    Returns: { 'cropped_size': int, 'sm': int, 'md': int, 'lg': int }  (bytes)
    """
    from io import BytesIO

    content = session.original_file.read()
    img = Image.open(BytesIO(content))

    # Убрать фон нейросетью
    has_alpha = False
    if session.remove_background:
        img_before = img.copy()
        img = _remove_background(img)
        has_alpha = True
        # Диагностика: сколько пикселей прозрачно (будет пересчитано после кропа)
        if img.mode == 'RGBA':
            alpha_full = img.split()[-1]
            total_full = alpha_full.size[0] * alpha_full.size[1]
            transparent_full = sum(1 for p in alpha_full.getdata() if p < 128)
            pct_full = round(transparent_full / total_full * 100, 1) if total_full else 0
        else:
            transparent_full, pct_full = 0, 0.0

    # Привести к RGB если нет прозрачности
    if not has_alpha:
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, hex_to_rgb(session.background_color))
            bg.paste(img, (0, 0), img)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

    # Crop + pad (RGBA canvas если есть прозрачность)
    cropped = crop_and_pad(
        img,
        session.crop_x, session.crop_y, session.crop_size,
        session.background_color, has_alpha=has_alpha,
    )

    # Диагностика: прозрачность внутри кадра
    crop_pct = 0.0
    if has_alpha and cropped.mode == 'RGBA':
        alpha_crop = cropped.split()[-1]
        total_c = alpha_crop.size[0] * alpha_crop.size[1]
        transp_c = sum(1 for p in alpha_crop.getdata() if p < 128)
        crop_pct = round(transp_c / total_c * 100, 1) if total_c else 0

    # Размер кропнутого (full-size, до ресайза)
    cropped_buf = BytesIO()
    cropped.save(cropped_buf, 'WEBP', quality=WEBP_QUALITY)
    cropped_size = cropped_buf.tell()

    # WebP
    sizes = {'cropped_size': cropped_size}
    variants = generate_webp_variants(cropped)
    original_name = session.original_file.name.rsplit('.', 1)[0]

    for suffix, buf in variants.items():
        field = getattr(session, f'result_{suffix}')
        filename = f'{original_name}_{WEBP_SIZES[suffix]}w.webp'
        field.save(filename, ContentFile(buf.read()), save=False)
        sizes[suffix] = buf.getbuffer().nbytes

    session.save(update_fields=['result_sm', 'result_md', 'result_lg'])
    result = dict(sizes)
    if session.remove_background:
        result['bg_removed_full_pct'] = pct_full
        result['bg_removed_crop_pct'] = crop_pct
    return result
