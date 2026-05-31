# image_processor/services.py
"""
Переиспользуемые инструменты обработки изображений и PDF.

Image pipeline (crop):
    1. Открыть оригинал (Pillow)
    2. [Опционально] Убрать фон нейросетью (rembg)
    3. Вырезать crop-область (crop_x, crop_y, crop_size)
    4. Добить фоном (background_color) — если рамка выходит за границы
    5. Сгенерировать WebP: sm(150), md(400), lg(800)

PDF pipeline:
    1. Рендерить страницу/страницы через PyMuPDF (fitz)
    2. Вернуть PIL Image для дальнейшей обработки
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


def resize_and_encode(image: Image.Image, width: int, fmt: str = 'webp',
                      quality: int = 80) -> BytesIO:
    """
    Ресайз изображения по ширине (пропорционально) и кодирование в целевой формат.
    
    Args:
        image:   PIL Image
        width:   целевая ширина в px
        fmt:     'webp', 'jpeg'/'jpg', 'png'
        quality: качество сжатия (для lossy-форматов)
    
    Returns BytesIO с закодированным изображением (указатель на начале).
    """
    variant = image.copy()
    w_percent = width / float(variant.size[0])
    h = int(float(variant.size[1]) * w_percent)
    variant = variant.resize((width, h), Image.LANCZOS)
    
    buf = BytesIO()
    fmt_lower = fmt.lower()
    
    if fmt_lower == 'webp':
        variant.save(buf, 'WEBP', quality=quality)
    elif fmt_lower in ('jpeg', 'jpg'):
        if variant.mode == 'RGBA':
            bg = Image.new('RGB', variant.size, (255, 255, 255))
            bg.paste(variant, (0, 0), variant)
            variant = bg
        elif variant.mode != 'RGB':
            variant = variant.convert('RGB')
        variant.save(buf, 'JPEG', quality=quality)
    elif fmt_lower == 'png':
        variant.save(buf, 'PNG')
    else:
        variant.save(buf, 'WEBP', quality=quality)
    
    buf.seek(0)
    return buf


def render_pdf_page(pdf_bytes: bytes, page_num: int = 0,
                    dpi: int = 150) -> Image.Image:
    """
    Рендерит одну страницу PDF в PIL Image (RGB).
    
    Args:
        pdf_bytes: сырые байты PDF-файла
        page_num:  номер страницы (0-based)
        dpi:       разрешение (150 = читаемый A4, 72 = превью)
    """
    try:
        import fitz
    except ImportError:
        raise RuntimeError('PyMuPDF (fitz) не установлен: pip install PyMuPDF')
    
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    if page_num >= len(doc):
        doc.close()
        raise IndexError(
            f'Страница {page_num} за пределами PDF (всего {len(doc)} стр.)'
        )
    page = doc[page_num]
    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    doc.close()
    return img


def _process_pdf_with_profile(pdf_bytes: bytes, profile: dict,
                               category_code: str) -> dict:
    """
    Render PDF pages and generate profile-based variants.
    
    Special handling for 'email' role: all pages re-rendered at email_dpi,
    combined into a single PDF preserving original page dimensions (A4 etc.).
    """
    import base64
    import fitz
    from io import BytesIO
    
    multi_page = profile.get('multi_page', False)
    render_dpi = profile.get('render_dpi', 150)
    email_dpi = profile.get('email_dpi', 0)
    
    # Separate email variants from per-page variants
    variants = profile.get('variants', [])
    has_email = any(vs['role'] == 'email' for vs in variants)
    page_variants = [vs for vs in variants if vs['role'] != 'email']
    
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    total = len(doc)
    max_pages = total if multi_page else 1
    
    pages = []
    for i in range(max_pages):
        page = doc[i]
        pix = page.get_pixmap(dpi=render_dpi)
        page_img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        
        page_entry = {'n': i + 1}
        for vs in page_variants:
            role = vs['role']
            role_variants = {}
            for w in vs['widths']:
                buf = resize_and_encode(page_img, w, vs['format'], vs['quality'])
                b64 = base64.b64encode(buf.read()).decode()
                fmt_lower = vs['format'].lower()
                mime_ext = 'jpeg' if fmt_lower in ('jpeg', 'jpg') else fmt_lower
                role_variants[str(w)] = {
                    'data': f'data:image/{mime_ext};base64,{b64}',
                    'size': buf.getbuffer().nbytes,
                    'format': vs['format'],
                    'width': w,
                }
            page_entry[role] = role_variants
        pages.append(page_entry)
    
    doc.close()
    
    result = {
        'category': category_code,
        'profile': profile,
        'pages': pages,
        'total_pages': total,
        'original_size': len(pdf_bytes),
    }
    
    # ── Email: re-render at email_dpi, combine into one PDF ──
    if has_email and email_dpi:
        email_doc = fitz.open(stream=pdf_bytes, filetype='pdf')
        out_pdf = fitz.open()
        
        for i in range(max_pages):
            page = email_doc[i]
            page_rect = page.rect  # original page size in points (e.g. A4: 595×842)
            pix = page.get_pixmap(dpi=email_dpi)
            img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
            
            buf = BytesIO()
            img.save(buf, 'JPEG', quality=60, optimize=True)
            buf.seek(0)
            
            out_page = out_pdf.new_page(width=page_rect.width, height=page_rect.height)
            out_page.insert_image(out_page.rect, stream=buf.read())
        
        email_doc.close()
        
        pdf_buf = BytesIO()
        out_pdf.save(pdf_buf, garbage=4, deflate=True)
        out_pdf.close()
        pdf_buf.seek(0)
        
        b64 = base64.b64encode(pdf_buf.read()).decode()
        result['email_pdf'] = {
            str(email_dpi): {
                'data': f'data:application/pdf;base64,{b64}',
                'size': pdf_buf.getbuffer().nbytes,
                'format': 'pdf',
                'dpi': email_dpi,
                'pages': max_pages,
            }
        }
    
    return result


def process_crop_session(session) -> dict:
    """
    Основной pipeline для ImageCropSession.
    Returns: { 'cropped_size': int, 'sm': int, 'md': int, 'lg': int }  (bytes)
    """
    from io import BytesIO

    content = session.original_file.read()
    img = Image.open(BytesIO(content))
    has_alpha = False
    pct_full = 0.0

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

    # Привести к RGB только если нет прозрачности
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


def process_with_profile(session, category_code: str) -> dict:
    """
    Process file (image or PDF) using a MediaCategory profile.
    
    Returns dict with base64-encoded variants (no DB writes).
    
    Images:  {'category':..., 'variants': {'icon':{'50':{...}}, ...}}
    PDF:     {'category':..., 'pages': [{'n':1, 'icon':{...}, 'page':{...}}, ...]}
    """
    import base64
    from io import BytesIO
    from media_library.models import MediaCategory
    
    profile = MediaCategory.get_profile(category_code)
    if not profile or not profile.get('variants'):
        return {'error': f'No profile or variants for category "{category_code}"'}
    
    content = session.original_file.read()
    
    # ── PDF branch ──
    if session.original_file.name.lower().endswith('.pdf'):
        return _process_pdf_with_profile(content, profile, category_code)
    
    # ── Image branch ──
    img = Image.open(BytesIO(content))
    has_alpha = False
    pct_full = 0.0
    
    if session.remove_background:
        img = _remove_background(img)
        has_alpha = True
        if img.mode == 'RGBA':
            alpha_full = img.split()[-1]
            total_full = alpha_full.size[0] * alpha_full.size[1]
            transparent_full = sum(1 for p in alpha_full.getdata() if p < 128)
            pct_full = round(transparent_full / total_full * 100, 1) if total_full else 0
    
    if not has_alpha:
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, hex_to_rgb(session.background_color))
            bg.paste(img, (0, 0), img)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
    
    # Crop + pad
    cropped = crop_and_pad(
        img, session.crop_x, session.crop_y, session.crop_size,
        session.background_color, has_alpha=has_alpha,
    )
    
    # ── Profile-based variants ──
    result = {
        'category': category_code,
        'profile': profile,
        'variants': {},
    }
    
    for vs in profile['variants']:
        role = vs['role']
        result['variants'][role] = {}
        for w in vs['widths']:
            buf = resize_and_encode(cropped, w, vs['format'], vs['quality'])
            b64 = base64.b64encode(buf.read()).decode()
            fmt_lower = vs['format'].lower()
            mime_ext = 'jpeg' if fmt_lower in ('jpeg', 'jpg') else fmt_lower
            result['variants'][role][str(w)] = {
                'data': f'data:image/{mime_ext};base64,{b64}',
                'size': buf.getbuffer().nbytes,
                'format': vs['format'],
                'width': w,
            }
    
    result['cropped_size'] = cropped.size[0] * cropped.size[1]  # pixels
    return result