"""
Распознавание чек-боксов в опросных листах / формах (универсальное, не привязано
к конкретному шаблону документа).

Обнаруживает напечатанные квадратные чек-боксы, определяет состояние
(отмечен крестом/галочкой или пуст) и связывает каждый с подписью справа.

Подход:
  * Детекция чек-боксов — по контурам (квадрат с 4 углами), а не по абсолютным
    координатам. Размер чек-бокса оценивается автоматически: фильтруются
    квадраты близкого размера (медианный кластер), поэтому алгоритм не зависит
    от разрешения/DPI скана.
  * Состояние — по доле «чернил» во внутренней области квадрата после
    бинаризации Оцу (масштаб-инвариантный признак).
  * Подпись — ближайшее OCR-слово справа на той же строке (RapidOCR, кириллица).

Зависимости: OpenCV + RapidOCR (onnxruntime). Без системного tesseract и torch —
удобно для переноса в Docker.

Все эвристические пороги вынесены в константы и/или параметры функции.
"""

import logging
from typing import Any , Dict , List

import numpy as np

logger = logging.getLogger(__name__)

# ── Параметры детекции ────────────────────────────────────────────────
# Широкий диапазон стороны квадрата (пиксели) для первичного отбора.
# Точный размер определяется кластеризацией, поэтому диапазон можно не трогать.
_MIN_SIDE = 8
_MAX_SIDE = 160

# Квадрат = 4 угла после аппроксимации контура.
_POLY_EPSILON = 0.03
# Контур должен существенно заполнять свой bounding box (рамка или заливка),
# а не быть тонким крестом/галочкой.
_MIN_FILL_RATIO = 0.45
# Допуск соотношения сторон.
_MIN_ASPECT , _MAX_ASPECT = 0.7 , 1.4

# Кластеризация по размеру: чек-боксы в форме одного размера. Оставляем те,
# чья сторона в пределах [0.65, 1.5] от медианной стороны.
_SIZE_LO , _SIZE_HI = 0.65 , 1.5

# Состояние: доля тёмных пикселей во внутренней области после бинаризации Оцу.
_INK_THRESHOLD = 0.08
# Внутренняя область (без рамки): отступ и ширина как доли стороны квадрата.
_INSET_FRACTION = 0.28
_INTERIOR_FRACTION = 0.44

# Подпись: слово справа, вертикально перекрывающее центр чек-бокса.
_LABEL_GAP = 4

# Группировка в строки: расстояние между центрами по Y (доли стороны чек-бокса).
_ROW_GAP_FRACTION = 1.2


def _load_image(data : bytes) :
    """Декодировать изображение в BGR (cv2.imdecode обходит не-ASCII пути)."""
    import cv2
    arr = np.frombuffer(data , dtype=np.uint8)
    img = cv2.imdecode(arr , cv2.IMREAD_COLOR)
    if img is None :
        raise ValueError('Не удалось декодировать изображение.')
    return img


def _ocr_words(img) -> List[Dict[str , Any]] :
    """OCR через RapidOCR (кириллица): список слов с координатами."""
    from rapidocr import RapidOCR

    from media_library.table_extractor import _rapidocr_params

    engine = RapidOCR(params=_rapidocr_params())
    result = engine(img)
    words : List[Dict[str , Any]] = []
    if result is None :
        return words

    boxes = getattr(result , 'boxes' , None)
    txts = getattr(result , 'txts' , None)
    scores = getattr(result , 'scores' , None)
    if boxes is None or txts is None or scores is None :
        return words

    for box , txt , score in zip(boxes , txts , scores) :
        xs = [int(p[0]) for p in box]
        ys = [int(p[1]) for p in box]
        words.append({
            'text' : txt ,
            'score' : float(score) ,
            'x1' : min(xs) , 'y1' : min(ys) ,
            'x2' : max(xs) , 'y2' : max(ys) ,
        })
    return words


def _detect_checkboxes(img) -> List[Dict[str , Any]] :
    """Найти квадратные чек-боксы и определить их состояние (масштаб-инвариантно)."""
    import cv2

    gray = cv2.cvtColor(img , cv2.COLOR_BGR2GRAY)

    # Контурная бинаризация (адаптивная) — для поиска рамок.
    blur = cv2.GaussianBlur(gray , (3 , 3) , 0)
    th = cv2.adaptiveThreshold(
        blur , 255 , cv2.ADAPTIVE_THRESH_MEAN_C , cv2.THRESH_BINARY_INV , 15 , 8
    )

    contours , _ = cv2.findContours(th , cv2.RETR_LIST , cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    for c in contours :
        x , y , w , h = cv2.boundingRect(c)
        if not (_MIN_SIDE <= w <= _MAX_SIDE and _MIN_SIDE <= h <= _MAX_SIDE) :
            continue
        aspect = w / h if h else 0
        if not (_MIN_ASPECT <= aspect <= _MAX_ASPECT) :
            continue
        perimeter = cv2.arcLength(c , True)
        if perimeter <= 0 :
            continue
        approx = cv2.approxPolyDP(c , _POLY_EPSILON * perimeter , True)
        if len(approx) != 4 :
            continue
        if cv2.contourArea(c) / (w * h) < _MIN_FILL_RATIO :
            continue
        candidates.append((x , y , w , h))

    if not candidates :
        return []

    # Кластеризация по размеру: отбрасываем квадраты, далёкие от медианного.
    sides = np.array([(w + h) / 2.0 for _ , _ , w , h in candidates])
    median = float(np.median(sides))
    if median <= 0 :
        return []
    lo , hi = median * _SIZE_LO , median * _SIZE_HI
    candidates = [
        c for c , s in zip(candidates , sides)
        if lo <= s <= hi
    ]

    # Дедупликация: внешняя (34x34) и внутренняя (28x28) рамки одного чек-бокса.
    def _iou(a , b) -> float :
        ax , ay , aw , ah = a
        bx , by , bw , bh = b
        ix1 , iy1 = max(ax , bx) , max(ay , by)
        ix2 , iy2 = min(ax + aw , bx + bw) , min(ay + ah , by + bh)
        iw , ih = max(0 , ix2 - ix1) , max(0 , iy2 - iy1)
        inter = iw * ih
        return inter / max(1 , aw * ah + bw * bh - inter)

    boxes = []
    for c in candidates :
        if not any(_iou(c , k) > 0.5 for k in boxes) :
            boxes.append(c)

    # Бинаризация Оцу для измерения «чернил» (устойчива к яркости/контрасту).
    _ , otsu = cv2.threshold(gray , 0 , 255 , cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    result = []
    for bx , by , bw , bh in boxes :
        ix = int(bx + bw * _INSET_FRACTION)
        iy = int(by + bh * _INSET_FRACTION)
        iw = max(1 , int(bw * _INTERIOR_FRACTION))
        ih = max(1 , int(bh * _INTERIOR_FRACTION))
        roi = otsu[iy:iy + ih , ix:ix + iw]
        ink = float(np.count_nonzero(roi)) / max(1 , roi.size)
        result.append({
            'x' : int(bx) , 'y' : int(by) , 'w' : int(bw) , 'h' : int(bh) ,
            'checked' : bool(ink > _INK_THRESHOLD) ,
            'ink_ratio' : round(ink , 3) ,
        })

    result.sort(key=lambda b : (b['y'] , b['x']))
    return result


def _associate_labels(checkboxes : List[Dict[str , Any]] ,
                      words : List[Dict[str , Any]]) -> None :
    """Проставить подпись: ближайшее слово справа, перекрывающее центр по Y."""
    for b in checkboxes :
        cy = b['y'] + b['h'] // 2
        right = b['x'] + b['w']
        candidates = [
            w for w in words
            if w['y1'] <= cy <= w['y2'] and w['x1'] >= right - _LABEL_GAP
        ]
        if candidates :
            candidates.sort(key=lambda w : w['x1'])
            b['label'] = candidates[0]['text']
        else :
            b['label'] = ''


def _group_rows(checkboxes : List[Dict[str , Any]]) -> List[Dict[str , Any]] :
    """Сгруппировать чек-боксы в строки по вертикальной близости."""
    if not checkboxes :
        return []
    side = float(np.median([(b['w'] + b['h']) / 2.0 for b in checkboxes]))
    gap = side * _ROW_GAP_FRACTION

    rows : List[Dict[str , Any]] = []
    for b in checkboxes :
        center = b['y'] + b['h'] / 2.0
        placed = False
        for r in rows :
            if abs(r['center'] - center) < gap :
                r['items'].append(b)
                placed = True
                break
        if not placed :
            rows.append({'center' : center , 'items' : [b]})

    out = []
    for r in rows :
        r['items'].sort(key=lambda b : b['x'])
        out.append({
            'y' : min(c['y'] for c in r['items']) ,
            'x' : min(c['x'] for c in r['items']) ,
            'selected' : [c['label'] for c in r['items'] if c['checked'] and c['label']] ,
            'options' : [
                {'label' : c['label'] , 'checked' : c['checked'] , 'x' : c['x'] , 'y' : c['y']}
                for c in r['items']
            ] ,
        })
    out.sort(key=lambda r : r['y'])
    return out


def extract_form_fields(data : bytes) -> Dict[str , Any] :
    """Распознать чек-боксы и их подписи на изображении (байты).

    Returns:
        {
            'checkboxes': [{'x','y','w','h','checked','ink_ratio','label'}, ...],
            'selected':  [подписи отмеченных чек-боксов, ...],
            'groups':    [{'y','x','selected','options':[{'label','checked'}, ...]}, ...],
        }
    """
    img = _load_image(data)
    checkboxes = _detect_checkboxes(img)
    if not checkboxes :
        return {'checkboxes' : [] , 'selected' : [] , 'groups' : []}

    try :
        words = _ocr_words(img)
    except Exception as e :
        logger.warning('OCR для подписей чек-боксов не выполнен: %s' , e)
        words = []

    _associate_labels(checkboxes , words)
    groups = _group_rows(list(checkboxes))

    return {
        'checkboxes' : checkboxes ,
        'selected' : [c['label'] for c in checkboxes if c['checked'] and c['label']] ,
        'groups' : groups ,
    }


def ocr_text_in_region(data : bytes , region) -> str :
    """Распознать текст внутри области «чек-бокс + подпись» (для ручной разметки).

    ``region`` — (x, y, w, h) в пикселях исходного изображения: область, которую
    пользователь обвёл вокруг чек-бокса вместе с его подписью. Квадрат чек-бокса
    (слева внутри области) исключается из OCR — распознаётся только текст.

    Возвращает строку подписи (может быть пустой).
    """
    img = _load_image(data)
    ih , iw = img.shape[:2]
    x , y , w , h = (int(v) for v in region)

    x1 , y1 = max(0 , x) , max(0 , y)
    x2 , y2 = min(iw , x + w) , min(ih , y + h)
    if x2 <= x1 or y2 <= y1 :
        return ''

    crop = img[y1:y2 , x1:x2]
    ch , cw = crop.shape[:2]

    # Квадрат чек-бокса в левой части области — пропускаем его при OCR.
    start_x = 0
    try :
        boxes = _detect_checkboxes(crop)
        left = [b for b in boxes if (b['x'] + b['w'] * 0.5) < cw * 0.5]
        if left :
            leftmost = min(left , key=lambda b : b['x'])
            start_x = min(cw , leftmost['x'] + leftmost['w'] + 2)
    except Exception :
        pass

    if start_x >= cw :
        return ''

    words = _ocr_words(crop[:, start_x:])
    if not words :
        return ''

    words.sort(key=lambda w : ((w['y1'] + w['y2']) / 2.0 , w['x1']))
    return ' '.join(w['text'] for w in words).strip()


def _words_to_lines(words : List[Dict[str , Any]]) -> List[Dict[str , Any]] :
    """Сгруппировать OCR-слова по строкам (по вертикальной близости)."""
    lines : List[Dict[str , Any]] = []
    for w in sorted(words , key=lambda w : ((w['y1'] + w['y2']) / 2.0 , w['x1'])) :
        cy = (w['y1'] + w['y2']) / 2.0
        h = w['y2'] - w['y1']
        placed = False
        for line in lines :
            if abs(line['cy'] - cy) < max(6 , h * 0.6) :
                line['words'].append(w)
                placed = True
                break
        if not placed :
            lines.append({'cy' : cy , 'words' : [w]})
    return sorted(lines , key=lambda l : l['cy'])


def _words_to_text(words : List[Dict[str , Any]]) -> str :
    """Собрать список OCR-слов в текст, группируя по строкам."""
    if not words :
        return ''
    out = []
    for line in _words_to_lines(words) :
        ws = sorted(line['words'] , key=lambda w : w['x1'])
        out.append(' '.join(w['text'] for w in ws))
    return '\n'.join(out)


def ocr_text_in_area(data : bytes , region) -> str :
    """OCR текста внутри прямоугольной области (без исключения чек-боксов).

    ``region`` — (x, y, w, h) в пикселях исходного изображения.
    """
    img = _load_image(data)
    ih , iw = img.shape[:2]
    x , y , w , h = (int(v) for v in region)
    x1 , y1 = max(0 , x) , max(0 , y)
    x2 , y2 = min(iw , x + w) , min(ih , y + h)
    if x2 <= x1 or y2 <= y1 :
        return ''
    return _words_to_text(_ocr_words(img[y1:y2 , x1:x2]))


def _has_table_grid(crop) -> bool :
    """Есть ли в области сетка таблицы (длинные горизонтальные линии).

    Таблица отличается от набора чек-боксов тем, что ячейки соединены
    горизонтальными (и вертикальными) линиями; чек-боксы — изолированные
    квадраты. Признак: >= 4 длинных горизонтальных линий.
    """
    import cv2
    gray = cv2.cvtColor(crop , cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray , (3 , 3) , 0)
    th = cv2.adaptiveThreshold(
        blur , 255 , cv2.ADAPTIVE_THRESH_MEAN_C , cv2.THRESH_BINARY_INV , 15 , 8
    )
    h , w = th.shape[:2]
    kl = max(24 , int(min(h , w) * 0.25))
    hk = cv2.getStructuringElement(cv2.MORPH_RECT , (kl , 1))
    hl = cv2.morphologyEx(th , cv2.MORPH_OPEN , hk)
    n_h = int((hl.mean(axis=1) > 60).sum())
    return n_h >= 4


def analyze_region(data : bytes , region) -> Dict[str , Any] :
    """Проанализировать область значения: таблица → чек-боксы → текст.

    Возвращает:
        {'type': 'table'|'checkboxes'|'text', 'text', 'table',
         'checkboxes', 'selected'}
    """
    empty = {'type' : 'text' , 'text' : '' , 'table' : None ,
             'checkboxes' : [] , 'selected' : []}

    img = _load_image(data)
    ih , iw = img.shape[:2]
    x , y , w , h = (int(v) for v in region)
    x1 , y1 = max(0 , x) , max(0 , y)
    x2 , y2 = min(iw , x + w) , min(ih , y + h)
    if x2 <= x1 or y2 <= y1 :
        return empty
    crop = img[y1:y2 , x1:x2]

    # 1) таблица — сетка из линий (проверяем первой: ячейки таблицы похожи на
    #    квадраты и иначе попадают в чек-боксы)
    if _has_table_grid(crop) :
        text = _words_to_text(_ocr_words(crop))
        return {
            'type' : 'table' , 'text' : text , 'table' : None ,
            'checkboxes' : [] , 'selected' : [] ,
        }

    # 2) чек-боксы
    checkboxes = _detect_checkboxes(crop)
    if checkboxes :
        words = _ocr_words(crop)
        _associate_labels(checkboxes , words)
        selected = [c['label'] for c in checkboxes if c['checked'] and c['label']]
        return {
            'type' : 'checkboxes' , 'text' : '' , 'table' : None ,
            'checkboxes' : checkboxes , 'selected' : selected ,
        }

    # 3) текст
    text = _words_to_text(_ocr_words(crop))
    return {'type' : 'text' , 'text' : text , 'table' : None ,
            'checkboxes' : [] , 'selected' : []}


def extract_fv_table(data : bytes , region) -> List[Dict[str , str]] :
    """Распознать таблицу из двух столбцов как список пар field-value.

    Каждая строка таблицы = одна пара {'field', 'value'}. Граница между
    столбцами ищется по максимальному горизонтальному разрыву между словами.
    """
    img = _load_image(data)
    ih , iw = img.shape[:2]
    x , y , w , h = (int(v) for v in region)
    x1 , y1 = max(0 , x) , max(0 , y)
    x2 , y2 = min(iw , x + w) , min(ih , y + h)
    if x2 <= x1 or y2 <= y1 :
        return []

    words = _ocr_words(img[y1:y2 , x1:x2])
    if not words :
        return []

    # Граница столбцов — максимальный разрыв между словами.
    boundary = None
    if len(words) >= 2 :
        xs = sorted(words , key=lambda w : w['x1'])
        best = 0
        for a , b in zip(xs , xs[1:]) :
            gap = b['x1'] - a['x2']
            if gap > best :
                best = gap
                boundary = (a['x2'] + b['x1']) / 2.0

    rows = []
    for line in _words_to_lines(words) :
        ws = sorted(line['words'] , key=lambda w : w['x1'])
        if boundary is None :
            field_words , value_words = ws , []
        else :
            field_words = [w for w in ws if w['x2'] <= boundary]
            value_words = [w for w in ws if w['x1'] >= boundary]
        field = ' '.join(w['text'] for w in field_words).strip()
        value = ' '.join(w['text'] for w in value_words).strip()
        if field or value :
            rows.append({'field' : field , 'value' : value})
    return rows
