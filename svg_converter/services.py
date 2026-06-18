# svg_converter/services.py
"""
Сервис векторизации растровых изображений в SVG.

Использует vtracer (https://github.com/visioncortex/vtracer) —
Rust-библиотека для трассировки line-art изображений в вектор.

Pipeline:
  1. Загрузка изображения (PIL)
  2. Предобработка: grayscale → threshold для ЧБ-режима
  3. Векторизация через vtracer
  4. Обрезка по выделенной области
  5. Возврат SVG-строки
"""
import logging
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)


def _read_file_content(session) -> bytes:
    """Прочитать содержимое файла сессии, сбросив указатель в начало."""
    session.original_file.seek(0)
    return session.original_file.read()


def pdf_to_svg_direct(file_content: bytes) -> str:
    """
    Извлечь векторный SVG напрямую из PDF через PyMuPDF.

    Если PDF содержит векторную графику — результат будет чисто векторным,
    без потерь качества трассировки. Если страница растровая — вернёт SVG
    с встроенным растром.
    """
    try:
        import fitz
        doc = fitz.open(stream=file_content, filetype='pdf')
        page = doc[0]
        svg = page.get_svg_image()
        doc.close()
        return svg
    except ImportError:
        raise RuntimeError('PyMuPDF (fitz) не установлен: pip install PyMuPDF')
    except Exception as e:
        raise RuntimeError(f'Ошибка извлечения SVG из PDF: {e}')


def open_image_or_pdf(file_content: bytes, filename: str = '') -> Image.Image:
    """
    Открыть файл как PIL Image — поддерживает JPG/PNG/WebP/BMP и PDF.

    Для PDF рендерит первую страницу через PyMuPDF (fitz).
    Возвращает RGB-изображение.
    """
    # Пробуем как обычное изображение
    try:
        img = Image.open(BytesIO(file_content))
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            return background
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return img
    except Exception as e:
        logger.debug(f'PIL open failed, trying PDF: {e}')
        pass

    # Пробуем как PDF
    if filename.lower().endswith('.pdf'):
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_content, filetype='pdf')
            page = doc[0]
            pix = page.get_pixmap(dpi=150)
            img = Image.open(BytesIO(pix.tobytes('ppm')))
            doc.close()
            return img.convert('RGB')
        except Exception:
            raise ValueError('Не удалось открыть файл — ни как изображение, ни как PDF.')

    raise ValueError(f'Неподдерживаемый формат: {filename}')


def preprocess_for_tracing(
    image: Image.Image,
    mode: str = 'bw',
    threshold: int = 128,
) -> Image.Image:
    """
    Предобработка изображения перед векторизацией.

    Для ЧБ-режима: vtracer сам бинаризует (colormode='binary'),
    поэтому только обесцвечиваем, без жёсткого порога.
    Порог используется для яркостной коррекции, но не для отсечки.

    Для цветного: без изменений.
    """
    if mode == 'bw':
        img = image.convert('L')  # grayscale
        # Лёгкая коррекция: подтягиваем контраст, не отсекаем
        img = img.point(lambda p: min(255, max(0, int((p - threshold) * 1.5 + 128))))
        return img.convert('RGB')
    return image.convert('RGB')


def _find_vtracer_binary() -> list:
    """
    Найти способ запуска vtracer.
    Возвращает список аргументов для subprocess: ['vtracer', ...] или ['python', '-m', 'vtracer', ...].
    Приоритет: бинарник в PATH, затем pip-установка, затем python -m vtracer.
    """
    import shutil
    import os
    import subprocess

    # 1. Проверить в PATH
    path = shutil.which('vtracer')
    if path:
        logger.debug(f'vtracer found in PATH: {path}')
        return [path]

    # 2. Проверить pip-установку (Python scripts)
    import sys
    scripts_dir = os.path.join(os.path.dirname(sys.executable), 'Scripts')
    for name in ['vtracer.exe', 'vtracer']:
        full = os.path.join(scripts_dir, name)
        if os.path.isfile(full):
            logger.debug(f'vtracer found: {full}')
            return [full]

    # 3. Проверить глобальную установку через cargo
    for name in ['vtracer.exe', 'vtracer']:
        full = os.path.expanduser(f'~/.cargo/bin/{name}')
        if os.path.isfile(full):
            logger.debug(f'vtracer found (cargo): {full}')
            return [full]

    # 4. Попробовать python -m vtracer
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'vtracer', '--version'],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 or 'vtracer' in (result.stdout + result.stderr).lower():
            logger.debug('vtracer available via python -m vtracer')
            return [sys.executable, '-m', 'vtracer']
    except Exception:
        pass

    return []


def raster_to_svg(
    image: Image.Image,
    mode: str = 'bw',
    threshold: int = 128,
) -> str:
    """
    Конвертировать PIL Image в SVG через vtracer Python API.

    vtracer Python-биндинг предоставляет convert_image_to_svg_py(in, out, ...) —
    файл-в-файл. Сохраняем предобработанное изображение во временный PNG,
    отдаём vtracer, читаем результат.

    Args:
        image: PIL Image (RGB)
        mode: 'bw' или 'color'
        threshold: порог бинаризации (0-255) для ЧБ-режима (предобработка,
                   не параметр vtracer)

    Returns:
        SVG-строка

    Raises:
        RuntimeError: если vtracer не установлен или упал
    """
    try:
        import vtracer
    except ImportError:
        raise RuntimeError(
            'vtracer не установлен. Выполните: pip install vtracer'
        )

    import tempfile
    import os

    processed = preprocess_for_tracing(image, mode, threshold)

    # Сохраняем предобработанное изображение во временный PNG
    tmp_in = None
    tmp_out = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            tmp_in = f.name
            processed.save(f, format='PNG')

        tmp_out = tmp_in + '.svg'

        vtracer.convert_image_to_svg_py(
            tmp_in,
            tmp_out,
            colormode='binary' if mode == 'bw' else 'color',
        )

        with open(tmp_out, 'r', encoding='utf-8') as f:
            svg = f.read()

        return svg

    except Exception as e:
        logger.error(f'vtracer conversion error: {e}')
        raise RuntimeError(f'Ошибка векторизации: {e}')

    finally:
        for p in [tmp_in, tmp_out]:
            if p and os.path.isfile(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass


def crop_svg(
    svg_content: str,
    x: float, y: float, w: float, h: float,
    img_w: int, img_h: int,
) -> str:
    """
    Обрезать SVG до указанной области через вложенный <svg> с viewBox.

    Вместо парсинга и модификации путей (сложно и ломко),
    оборачиваем оригинальный SVG в родительский с viewBox-областью.
    Масштабируется корректно при любом размере контейнера.
    """
    # Вычисляем viewBox в координатах оригинального SVG
    # Предполагаем, что vtracer выдаёт SVG с размерами исходного изображения
    viewbox = f'{x:.0f} {y:.0f} {w:.0f} {h:.0f}'

    # Оборачиваем — сохраняем исходный SVG как есть, но с viewBox-областью
    # Убираем возможный xmlns из вложенного (vtracer добавляет)
    inner = svg_content
    # Удаляем <?xml ...?> и <!DOCTYPE ...> из вложенного
    if inner.startswith('<?xml'):
        start = inner.find('<svg')
        if start != -1:
            inner = inner[start:]

    wrapped = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="{viewbox}"
     width="{w:.0f}" height="{h:.0f}">
  {inner}
</svg>'''

    return wrapped


def process_svg_conversion(session) -> str:
    """
    Полный pipeline: загрузить → предобработать → векторизовать → обрезать.

    Args:
        session: SvgConversionSession instance

    Returns:
        SVG-строка
    """
    content = _read_file_content(session)
    is_pdf = session.original_filename.lower().endswith('.pdf') if session.original_filename else False
    is_direct_pdf_vector = False

    if is_pdf:
        try:
            svg = pdf_to_svg_direct(content)
            is_direct_pdf_vector = True
        except Exception:
            img = open_image_or_pdf(content, session.original_filename or '')
            session.original_width, session.original_height = img.size
            svg = raster_to_svg(img, mode=session.color_mode, threshold=session.threshold)
    else:
        img = open_image_or_pdf(content, session.original_filename or '')
        session.original_width, session.original_height = img.size
        svg = raster_to_svg(img, mode=session.color_mode, threshold=session.threshold)

    # Обрезка — только для vtracer-результатов; PDF-вектор идёт целиком
    if not is_direct_pdf_vector and all(
        session.region_x is not None,
        session.region_y is not None,
        session.region_w is not None,
        session.region_h is not None,
    ):
        w = session.original_width or 1000
        h = session.original_height or 1000
        svg = crop_svg(
            svg,
            session.region_x, session.region_y,
            session.region_w, session.region_h,
            w, h,
        )

    return svg