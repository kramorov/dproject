#!/usr/bin/env python3
"""Заливка русского перевода обратно в PyInstaller exe (Python 3.11).

Без декомпиляции: патчит строковые константы в code-объектах (marshal +
code.replace), пересобирает вложенный PYZ-архив и внешний CArchive, пишет
новый exe с русским интерфейсом.

Патчатся ровно два прикладных модуля:
  * qt_app  — главный скрипт (лежит в CArchive, тип 's');
  * engine  — движок расчёта (лежит в PYZ, тип 'm').

Запуск ТОЛЬКО под Python 3.11 (той же версии, под которой собран exe):
    C:\\Python311\\python.exe apply_translation.py app.exe translate.json app_ru.exe

Зависимости: стандартная библиотека + pyc_strings.py (рядом).
"""

import marshal
import struct
import sys
import zlib

import pyc_strings

MAGIC = b'MEI\014\013\012\013\016'
COOKIE_SIZE = 88
PYZ_MAGIC = b'PYZ\x00'
TOC_HDR = struct.calcsize('!iIIIBc')  # 18


# --------------------------------------------------------------------------- #
# CArchive (внешний, в exe)
# --------------------------------------------------------------------------- #
def parse_carchive(data):
    cookie_pos = data.rfind(MAGIC)
    if cookie_pos < 0:
        raise ValueError('Не найден CArchive cookie (MEI).')
    (_, lengthofPackage, toc, toc_len, pyver, pylibname) = struct.unpack(
        '!8sIIii64s', data[cookie_pos:cookie_pos + COOKIE_SIZE])
    # lengthofPackage включает файлы + TOC + cookie (88 байт).
    pkg_start = cookie_pos + COOKIE_SIZE - lengthofPackage
    toc_pos = pkg_start + toc

    entries = []
    p = toc_pos
    end = toc_pos + toc_len
    while p < end:
        (entry_size,) = struct.unpack('!i', data[p:p + 4])
        (entry_pos, cmprsd_size, uncmprsd_size, flag, typ, name) = struct.unpack(
            '!IIIBc%ds' % (entry_size - TOC_HDR), data[p + 4:p + entry_size])
        name = name.decode('utf-8').rstrip('\x00')
        raw = data[pkg_start + entry_pos: pkg_start + entry_pos + cmprsd_size]
        entries.append({
            'name': name,
            'type': typ,
            'flag': flag,
            'cmprsd_size': cmprsd_size,
            'uncmprsd_size': uncmprsd_size,
            'raw': raw,
        })
        p += entry_size

    return {
        'pkg_start': pkg_start,
        'pyver': pyver,
        'pylibname': pylibname,
        'entries': entries,
    }


def _unpack(entry):
    return zlib.decompress(entry['raw']) if entry['flag'] == 1 else entry['raw']


def _pack(entry, uncompressed):
    return zlib.compress(uncompressed, 9) if entry['flag'] == 1 else uncompressed


def rebuild_carchive(parsed, entries_data):
    """entries_data: {name: new uncompressed bytes}. Возвращает новый пакет."""
    files_buf = bytearray()
    toc_buf = bytearray()

    for entry in parsed['entries']:
        uncompressed = entries_data.get(entry['name'], _unpack(entry))
        raw = _pack(entry, uncompressed)
        entry_pos = len(files_buf)
        files_buf += raw

        name_b = entry['name'].encode('utf-8')
        # размер TOC-записи выравнивается до 16 байт (как в PyInstaller)
        body_len = TOC_HDR + len(name_b)
        entry_size = (body_len + 15) & ~15
        record = (
            struct.pack('!iIIIBc', entry_size, entry_pos, len(raw),
                        len(uncompressed), entry['flag'], entry['type'])
            + name_b
            + b'\x00' * (entry_size - body_len)
        )
        toc_buf += record

    files_len = len(files_buf)
    toc_len = len(toc_buf)
    lengthofPackage = files_len + toc_len + COOKIE_SIZE

    cookie = struct.pack(
        '!8sIIii64s',
        MAGIC, lengthofPackage, files_len, toc_len,
        parsed['pyver'], parsed['pylibname'],
    )
    return bytes(files_buf) + bytes(toc_buf) + cookie


# --------------------------------------------------------------------------- #
# PYZ (вложенный архив кода)
# --------------------------------------------------------------------------- #
def parse_pyz(pyz_data):
    assert pyz_data[:4] == PYZ_MAGIC, 'Некорректный PYZ-магический байт'
    pyc_magic = pyz_data[4:8]
    (toc_pos,) = struct.unpack('!i', pyz_data[8:12])
    toc = marshal.loads(pyz_data[toc_pos:])  # list of (name, (ispkg, pos, length))
    return {'pyc_magic': pyc_magic, 'toc': toc, 'data': pyz_data}


def rebuild_pyz(parsed, mapping):
    toc = parsed['toc']
    data = parsed['data']
    # префикс: 8 байт (PYZ\0 + magic) + 4 байта toc_pos + промежуток до данных
    data_start = min(pos for _name, (_ispkg, pos, _length) in toc)

    buf = bytearray()
    new_toc = []
    for name, (ispkg, _pos, _length) in toc:
        raw = data[_pos:_pos + _length]
        code = marshal.loads(zlib.decompress(raw))
        code = pyc_strings.replace_string_consts(code, mapping)
        compressed = zlib.compress(marshal.dumps(code), 9)
        new_pos = data_start + len(buf)
        buf += compressed
        new_toc.append((name, (ispkg, new_pos, len(compressed))))

    toc_bytes = marshal.dumps(new_toc)
    new_toc_pos = data_start + len(buf)

    return (
        data[:8]
        + struct.pack('!i', new_toc_pos)
        + data[12:data_start]
        + bytes(buf)
        + toc_bytes
    )


# --------------------------------------------------------------------------- #
# Патч code-объектов
# --------------------------------------------------------------------------- #
def patch_code_obj(data, mapping):
    code = marshal.loads(data)
    code = pyc_strings.replace_string_consts(code, mapping)
    return marshal.dumps(code)


def count_replaced(code_obj, mapping):
    total = 0
    for text, _name in pyc_strings.iter_string_consts(code_obj):
        if text in mapping:
            total += 1
    return total


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(2)

    exe_path, translate_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(translate_path, 'r', encoding='utf-8') as f:
        mapping = json_load(f)
    data = open(exe_path, 'rb').read()

    print('[1/3] Разбор CArchive…')
    parsed = parse_carchive(data)
    names = [e['name'] for e in parsed['entries']]
    print('      Записей:', len(names))

    entries_data = {}
    replaced_qt = 0
    replaced_engine = 0

    for entry in parsed['entries']:
        if entry['name'] == 'qt_app':
            print('[2/3] Патч qt_app…')
            uncompressed = _unpack(entry)
            replaced_qt = count_replaced(marshal.loads(uncompressed), mapping)
            entries_data['qt_app'] = patch_code_obj(uncompressed, mapping)
        elif entry['name'] == 'PYZ.pyz':
            print('[2/3] Патч PYZ (engine)…')
            pyz = parse_pyz(_unpack(entry))
            pyz_patched = rebuild_pyz(pyz, mapping)
            entries_data['PYZ.pyz'] = pyz_patched
            # сколько строк заменено в engine — по TOC
            for name, (_ispkg, pos, length) in pyz['toc']:
                if name == 'engine':
                    code = marshal.loads(zlib.decompress(pyz['data'][pos:pos + length]))
                    replaced_engine = count_replaced(code, mapping)

    print('[3/3] Пересборка exe…')
    new_package = rebuild_carchive(parsed, entries_data)
    with open(out_path, 'wb') as f:
        f.write(data[:parsed['pkg_start']])
        f.write(new_package)

    print('      Заменено строк в qt_app:', replaced_qt)
    print('      Заменено строк в engine:', replaced_engine)
    print('      Результат:', out_path)


def json_load(f):
    import json
    return json.load(f)


if __name__ == '__main__':
    main()
