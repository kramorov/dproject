"""
Экспорт размеченной структуры опросного листа (JSON-дерева) в Word/Excel.

Входной формат — дерево узлов:
    {
      "items": [
        {"kind": "section", "title": "...", "children": [ ... ]},
        {"kind": "field",  "field": "...", "values": [ value, ... ]},
        {"kind": "table",  "rows": [ {"field": "...", "value": "..."}, ... ]}
      ]
    }

    value = {"type": "text"|"checkboxes"|"table", "text": "...",
             "selected": [...], "options": [{"label","checked"}, ...]}
"""

from io import BytesIO
from typing import Any , Dict , List , Tuple


def _flatten_value(value : Dict[str , Any]) -> str :
    """Привести значение к строке."""
    kind = value.get('type' , 'text')
    if kind == 'checkboxes' :
        selected = value.get('selected') or []
        if selected :
            return ', '.join(str(s) for s in selected)
        options = value.get('options') or []
        checked = [o.get('label' , '') for o in options if o.get('checked')]
        return ', '.join(str(c) for c in checked if c)
    return (value.get('text') or '').strip()


def _iter_pairs(items : List[Dict[str , Any]] ,
                section_path : str = '' ,
                out : List[Tuple[str , str , str]] | None = None) -> List[Tuple[str , str , str]] :
    """Развернуть дерево в плоский список (раздел, поле, значение)."""
    if out is None :
        out = []
    for item in items :
        kind = item.get('kind')
        if kind == 'section' :
            title = item.get('title') or ''
            path = (section_path + ' / ' + title) if section_path else title
            _iter_pairs(item.get('children') or [] , path , out)
        elif kind == 'field' :
            field = item.get('field') or ''
            values = item.get('values') or []
            if not values :
                out.append((section_path , field , ''))
            for v in values :
                out.append((section_path , field , _flatten_value(v)))
        elif kind == 'table' :
            for row in item.get('rows') or [] :
                out.append((section_path , row.get('field' , '') , row.get('value' , '')))
    return out


def structure_to_xlsx(structure : Dict[str , Any]) -> bytes :
    """Структура → Excel (bytes): колонки Раздел / Поле / Значение."""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = 'ОЛ'
    ws.append(['Раздел' , 'Поле' , 'Значение'])
    for path , field , value in _iter_pairs(structure.get('items') or []) :
        ws.append([path , field , value])
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _render_docx_items(doc , items : List[Dict[str , Any]] , level : int = 0) -> None :
    for item in items :
        kind = item.get('kind')
        if kind == 'section' :
            doc.add_heading(item.get('title') or '' , level=min(level + 1 , 4))
            _render_docx_items(doc , item.get('children') or [] , level + 1)
        elif kind == 'field' :
            field = item.get('field') or ''
            values = item.get('values') or []
            if values :
                for v in values :
                    doc.add_paragraph(f'{field}: {_flatten_value(v)}')
            else :
                doc.add_paragraph(field)
        elif kind == 'table' :
            rows = item.get('rows') or []
            if rows :
                table = doc.add_table(rows=1 , cols=2)
                table.style = 'Table Grid'
                table.rows[0].cells[0].text = 'Поле'
                table.rows[0].cells[1].text = 'Значение'
                for row in rows :
                    cells = table.add_row().cells
                    cells[0].text = row.get('field' , '') or ''
                    cells[1].text = row.get('value' , '') or ''


def structure_to_docx(structure : Dict[str , Any]) -> bytes :
    """Структура → Word (bytes): заголовки разделов, пары field: value, таблицы."""
    from docx import Document
    doc = Document()
    _render_docx_items(doc , structure.get('items') or [])
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()
