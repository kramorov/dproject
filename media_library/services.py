# media_library/services.py
"""
Оркестратор генерации вариантов для MediaLibraryItem.

Читает профиль из item.category.profile (MediaCategory.PRESENTATION_PROFILES),
вызывает инструменты из image_processor.services, создаёт MediaVariant через through-модель.
"""
import logging
from io import BytesIO
from PIL import Image
from django.apps import apps
from django.core.files.base import ContentFile
from storage_manager.services import file_service
from image_processor.services import resize_and_encode, render_pdf_page

logger = logging.getLogger(__name__)


def _save_to_storage(item, buf: BytesIO, role: str, width: int, fmt: str,
                     page_num: int = None) -> tuple[str, int]:
    """Сохранить вариант в хранилище, вернуть (путь, размер_в_байтах)."""
    ext = 'jpg' if fmt.lower() in ('jpeg', 'jpg') else fmt.lower()
    prefix = f'p{page_num}_' if page_num is not None else ''
    path = f'media_library/variants/{item.pk}/{prefix}{role}_{width}.{ext}'
    size = buf.getbuffer().nbytes
    file_service.storage.save(path, ContentFile(buf.read()))
    buf.seek(0)
    return path, size


def _compute_height(orig_size: tuple[int, int], target_width: int) -> int:
    """Вычислить высоту после пропорционального ресайза по ширине."""
    return int(float(orig_size[1]) * target_width / float(orig_size[0]))


def generate_variants(item, source_file=None) -> int:
    """
    Сгенерировать все варианты для MediaLibraryItem согласно профилю категории.

    Создаёт строки MediaVariant в БД. Файлы сохраняются в Cloud.ru.
    Возвращает количество созданных вариантов.

    Args:
        item: MediaLibraryItem
        source_file: опциональный file-like object. Если передан, варианты
                     генерируются из него, а не из item.media_file.

    Изображения: role=icon/thumb/card/full, width=50/150/400...
    PDF: role=icon/page/email + page_num=N
    """
    MediaVariant = apps.get_model('media_library', 'MediaVariant')

    profile = item.category.profile
    if not profile or not profile.get('variants'):
        return 0

    is_pdf = item._is_pdf()
    is_img = item.is_image()
    if not (is_pdf or is_img):
        return 0

    created = 0

    content = source_file.read() if source_file else (item.media_file.read() if item.media_file else None)

    if is_pdf:
        import fitz
        multi_page = profile.get('multi_page', False)
        render_dpi = profile.get('render_dpi', 150)
        email_dpi = profile.get('email_dpi', 0)

        doc = fitz.open(stream=content, filetype='pdf')
        total_pages = len(doc)
        max_pages = total_pages if multi_page else 1

        # Отделяем email от постраничных вариантов
        variants = profile.get('variants', [])
        email_variants = [vs for vs in variants if vs['role'] == 'email']
        page_variants = [vs for vs in variants if vs['role'] != 'email']

        # ── Постраничные варианты (icon, page) ──
        for i in range(max_pages):
            try:
                page_img = render_pdf_page(content, page_num=i, dpi=render_dpi)
            except Exception as e:
                logger.warning(f'Ошибка рендера страницы {i+1} для item {item.pk}: {e}')
                continue

            orig_w, orig_h = page_img.size

            for vs in page_variants:
                role = vs['role']
                fmt = vs['format']
                quality = vs['quality']
                for w in vs['widths']:
                    buf = resize_and_encode(page_img, w, fmt, quality)
                    path, size = _save_to_storage(item, buf, role, w, fmt,
                                                  page_num=i + 1)
                    h = _compute_height((orig_w, orig_h), w)
                    MediaVariant.objects.create(
                        media_item=item, role=role, width=w, height=h,
                        format=fmt, file_path=path, file_size=size, page_num=i + 1,
                    )
                    created += 1

        # ── Email: сжатый PDF (все страницы, низкое dpi, JPEG quality=60) ──
        if email_variants and email_dpi:
            try:
                email_doc = fitz.open(stream=content, filetype='pdf')
                out_pdf = fitz.open()

                for i in range(max_pages):
                    page = email_doc[i]
                    page_rect = page.rect
                    pix = page.get_pixmap(dpi=email_dpi)
                    img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)

                    buf_jpg = BytesIO()
                    img.save(buf_jpg, 'JPEG', quality=60, optimize=True)
                    buf_jpg.seek(0)

                    out_page = out_pdf.new_page(width=page_rect.width, height=page_rect.height)
                    out_page.insert_image(out_page.rect, stream=buf_jpg.read())

                email_doc.close()

                pdf_buf = BytesIO()
                out_pdf.save(pdf_buf, garbage=4, deflate=True)
                out_pdf.close()
                pdf_buf.seek(0)

                path = f'media_library/variants/{item.pk}/email_compressed.pdf'
                size = pdf_buf.getbuffer().nbytes
                file_service.storage.save(path, ContentFile(pdf_buf.read()))

                MediaVariant.objects.create(
                    media_item=item, role='email', width=800, height=0,
                    format='pdf', file_path=path, file_size=size, page_num=1,
                )
                created += 1
                logger.info(f'Сгенерирован email PDF для {item.pk}: {size} байт')
            except Exception as e:
                logger.warning(f'Ошибка генерации email PDF для {item.pk}: {e}')

        doc.close()
        logger.info(f'Сгенерированы варианты PDF: {item.pk}, страниц: {max_pages}, вариантов: {created}')

    elif is_img:
        if not content: return 0
        img = Image.open(BytesIO(content))
        orig_w, orig_h = img.size

        if profile.get('keep_alpha') and img.mode != 'RGBA':
            img = img.convert('RGBA')
        elif not profile.get('keep_alpha') and img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, (0, 0), img)
            img = bg

        for vs in profile['variants']:
            role = vs['role']
            fmt = vs['format']
            quality = vs['quality']
            for w in vs['widths']:
                buf = resize_and_encode(img, w, fmt, quality)
                path, size = _save_to_storage(item, buf, role, w, fmt)
                h = _compute_height((orig_w, orig_h), w)
                MediaVariant.objects.create(
                    media_item=item,
                    role=role,
                    width=w,
                    height=h,
                    format=fmt,
                    file_path=path,
                    file_size=size,
                )
                created += 1

        logger.info(f'Сгенерированы варианты изображения: {item.pk}, вариантов: {created}')

    return created


def delete_variants(item):
    """Удалить все варианты из хранилища и БД (при замене файла)."""
    for v in item.variants.all():
        if v.file_path:
            try:
                file_service.delete_file(v.file_path)
            except Exception as e:
                logger.warning(f'Не удалось удалить variant {v.pk} ({v.file_path}): {e}')
    item.variants.all().delete()


def get_variants_for_api(item) -> dict:
    """
    Вернуть variants с URL вместо путей — для API.

    Изображения:  {'icon': {'50': 'url'}, 'card': {'400': 'url', '800': 'url'}, ...}
    PDF:  {'pages': [{n:1, 'icon':{...}, 'page':{...}}, ...], 'email_pdf': 'url', 'total_pages': N}
    """
    qs = item.variants.all().order_by('page_num', 'role', 'width')
    if not qs.exists():
        return {}

    has_pages = qs.filter(page_num__isnull=False).exists()

    if has_pages:
        result = {'pages': [], 'total_pages': 0}
        pages_map = {}
        email_url = None
        for v in qs:
            if v.page_num is None:
                continue
            # email — отдельно, не по страницам
            if v.role == 'email' and v.format == 'pdf':
                email_url = file_service.get_file_url(v.file_path)
                continue
            pn = v.page_num
            if pn not in pages_map:
                pages_map[pn] = {'n': pn}
            if v.role not in pages_map[pn]:
                pages_map[pn][v.role] = {}
            pages_map[pn][v.role][str(v.width)] = file_service.get_file_url(v.file_path)
        result['pages'] = sorted(pages_map.values(), key=lambda p: p['n'])
        result['total_pages'] = len(result['pages'])
        if email_url:
            result['email_pdf'] = email_url
        return result
    else:
        result = {}
        for v in qs:
            if v.role not in result:
                result[v.role] = {}
            result[v.role][str(v.width)] = file_service.get_file_url(v.file_path)
        return result