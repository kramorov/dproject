# media_library/services.py
"""
Оркестратор генерации вариантов для MediaLibraryItem.

Читает профиль из item.category.profile (MediaCategory.PRESENTATION_PROFILES),
вызывает инструменты из image_processor.services, сохраняет результаты в хранилище.
"""
import logging
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from storage_manager.services import file_service
from image_processor.services import resize_and_encode, render_pdf_page

logger = logging.getLogger(__name__)


def _save_to_storage(item, buf: BytesIO, role: str, width: int, fmt: str,
                     page_num: int = None) -> str:
    """Сохранить вариант в хранилище, вернуть путь."""
    ext = 'jpg' if fmt.lower() in ('jpeg', 'jpg') else fmt.lower()
    prefix = f'p{page_num}_' if page_num is not None else ''
    path = f'media_library/variants/{item.pk}/{prefix}{role}_{width}.{ext}'
    file_service.storage.save(path, ContentFile(buf.read()))
    buf.seek(0)
    return path


def generate_variants(item) -> dict:
    """
    Сгенерировать все варианты для MediaLibraryItem согласно профилю категории.

    Сохраняет файлы в хранилище, возвращает словарь для item.variants.

    Изображения:  {'icon': {'50': 'path'}, 'card': {'150': 'path', ...}, ...}
    PDF:  {'pages': [{n:1, 'icon':{...}, 'page':{...}}, ...], 'total_pages': N}
    """
    profile = item.category.profile
    if not profile or not profile.get('variants'):
        return {}

    is_pdf = item._is_pdf()
    is_img = item.is_image()
    if not (is_pdf or is_img):
        return {}

    result = {}

    if is_pdf:
        content = item.media_file.read()
        multi_page = profile.get('multi_page', False)
        render_dpi = profile.get('render_dpi', 150)

        # Определяем количество страниц
        try:
            import fitz
            doc = fitz.open(stream=content, filetype='pdf')
            total_pages = len(doc)
            doc.close()
        except Exception:
            total_pages = 1
        max_pages = total_pages if multi_page else 1

        pages = []
        for i in range(max_pages):
            try:
                page_img = render_pdf_page(content, page_num=i, dpi=render_dpi)
            except Exception as e:
                logger.warning(f'Ошибка рендера страницы {i+1} для item {item.pk}: {e}')
                continue

            page_entry = {'n': i + 1}
            for vs in profile['variants']:
                role = vs['role']
                role_variants = {}
                for w in vs['widths']:
                    buf = resize_and_encode(page_img, w, vs['format'], vs['quality'])
                    path = _save_to_storage(item, buf, role, w, vs['format'],
                                            page_num=i + 1)
                    role_variants[str(w)] = path
                page_entry[role] = role_variants
            pages.append(page_entry)

        result['pages'] = pages
        result['total_pages'] = total_pages
        logger.info(f'Сгенерированы варианты PDF: {item.pk}, страниц: {len(pages)}')

    elif is_img:
        content = item.media_file.read()
        img = Image.open(BytesIO(content))

        if profile.get('keep_alpha') and img.mode != 'RGBA':
            img = img.convert('RGBA')
        elif not profile.get('keep_alpha') and img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, (0, 0), img)
            img = bg

        for vs in profile['variants']:
            role = vs['role']
            role_variants = {}
            for w in vs['widths']:
                buf = resize_and_encode(img, w, vs['format'], vs['quality'])
                path = _save_to_storage(item, buf, role, w, vs['format'])
                role_variants[str(w)] = path
            result[role] = role_variants

        logger.info(f'Сгенерированы варианты изображения: {item.pk}')

    return result


def delete_variants(item):
    """Удалить все варианты из хранилища (при удалении item или замене файла)."""
    if not item.variants:
        return
    paths = _collect_variant_paths(item.variants)
    for p in paths:
        try:
            file_service.delete_file(p)
        except Exception as e:
            logger.warning(f'Не удалось удалить variant {p}: {e}')


def _collect_variant_paths(variants: dict) -> list:
    """Собрать все пути файлов из словаря variants."""
    paths = []
    if 'pages' in variants:
        for page in variants['pages']:
            for role, sizes in page.items():
                if role == 'n':
                    continue
                if isinstance(sizes, dict):
                    paths.extend(sizes.values())
    else:
        for role, sizes in variants.items():
            if isinstance(sizes, dict):
                paths.extend(sizes.values())
    return paths


def get_variants_for_api(item) -> dict:
    """
    Вернуть variants с URL вместо путей — для API.
    """
    if not item.variants:
        return {}
    result = {}
    if 'pages' in item.variants:
        result['pages'] = []
        for page in item.variants['pages']:
            page_out = {'n': page['n']}
            for role, sizes in page.items():
                if role == 'n':
                    continue
                if isinstance(sizes, dict):
                    page_out[role] = {
                        w: file_service.get_file_url(path)
                        for w, path in sizes.items()
                    }
            result['pages'].append(page_out)
        result['total_pages'] = item.variants.get('total_pages', len(result['pages']))
    else:
        for role, sizes in item.variants.items():
            if isinstance(sizes, dict):
                result[role] = {
                    w: file_service.get_file_url(path)
                    for w, path in sizes.items()
                }
    return result
