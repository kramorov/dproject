"""Чтение/запись строковых констант в .pyc-файлах PyInstaller (Python 3.11).

Рекурсивно обходит code-объекты ВКЛЮЧАЯ строки, вложенные в кортежи и frozenset
(в co_consts списки/кортежи опций хранятся именно так). Работает ТОЛЬКО под той
же версией Python, под которой собран exe (3.11).
"""

import marshal
import types

PYC_HEADER_SIZE = 16


def is_cjk(s: str) -> bool:
    """Есть ли в строке хотя бы один китайский (CJK) иероглиф."""
    return any('\u4e00' <= ch <= '\u9fff' for ch in s)


def read_code(path):
    """Читает .pyc и возвращает корневой code-объект."""
    with open(path, 'rb') as f:
        data = f.read()
    return marshal.loads(data[PYC_HEADER_SIZE:])


def read_header(path):
    """Возвращает первые 16 байт (заголовок .pyc), чтобы переиспользовать при записи."""
    with open(path, 'rb') as f:
        return f.read(PYC_HEADER_SIZE)


def iter_string_consts(code, name=''):
    """Рекурсивно обходит code-объект и возвращает (строка, имя_объекта)."""
    for const in code.co_consts:
        yield from _iter_const(const, name)


def _iter_const(const, name):
    if isinstance(const, str):
        yield const, name
    elif isinstance(const, types.CodeType):
        child = f'{name}.{const.co_name}' if name else const.co_name
        for c in const.co_consts:
            yield from _iter_const(c, child)
    elif isinstance(const, (tuple, frozenset, list, set)):
        for i, c in enumerate(const):
            yield from _iter_const(c, f'{name}[{i}]')
    elif isinstance(const, dict):
        for k, v in const.items():
            yield from _iter_const(k, f'{name}.key')
            yield from _iter_const(v, f'{name}.val')
    # bytes, int, float, complex, bool, None, Ellipsis — пропускаем


def replace_string_consts(code, mapping):
    """Возвращает новый code-объект, в котором строки заменены по mapping.

    Рекурсивно перестраивает вложенные code-объекты и контейнеры (кортежи,
    frozenset и т.д.), сохраняя остальные поля.
    """
    new_consts = []
    for const in code.co_consts:
        new_consts.append(_replace_const(const, mapping))
    return code.replace(co_consts=tuple(new_consts))


def _replace_const(const, mapping):
    if isinstance(const, str):
        return mapping.get(const, const)
    if isinstance(const, types.CodeType):
        return replace_string_consts(const, mapping)
    if isinstance(const, tuple):
        return tuple(_replace_const(c, mapping) for c in const)
    if isinstance(const, frozenset):
        return frozenset(_replace_const(c, mapping) for c in const)
    if isinstance(const, list):
        return [_replace_const(c, mapping) for c in const]
    if isinstance(const, set):
        return {_replace_const(c, mapping) for c in const}
    if isinstance(const, dict):
        return {_replace_const(k, mapping): _replace_const(v, mapping)
                for k, v in const.items()}
    return const


def write_code(path, code_obj, header):
    """Пишет code-объект обратно в .pyc, сохраняя оригинальный 16-байтный заголовок."""
    with open(path, 'wb') as f:
        f.write(header)
        f.write(marshal.dumps(code_obj))
