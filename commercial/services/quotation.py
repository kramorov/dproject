# commercial/services/quotation.py
"""
Сборка КП из корзины: docxtpl рендерит шапку-шаблон (логотип/текст/реквизиты),
а табличная и описательная части добавляются программно (python-docx).
"""
import io
from decimal import Decimal, InvalidOperation
from pathlib import Path

from docxtpl import DocxTemplate
from django.utils import timezone

from cart.serializers import CartItemSerializer
from .numbering import generate_quotation_number

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / 'templates' / 'quotation_template.docx'

TABLE_HEADERS = ['№ подпункта', 'Артикул', 'Описание', 'Количество', 'Цена, руб', 'Сумма, руб']


def _fmt_money(value):
    """1250.5 -> '1 250,50'."""
    try:
        value = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        value = Decimal('0')
    s = f"{value:,.2f}"
    return s.replace(',', ' ').replace('.', ',')


def _to_decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def _extract_spec_rows(sku, fallback_specs):
    """Спецификации уникального товара: предпочтительно из to_dict() модели."""
    source = getattr(sku, 'source_object', None)
    if source is not None and hasattr(source, 'to_dict'):
        try:
            data = source.to_dict()
            for section in data.get('sections', []) or []:
                if section.get('type') != 'specs':
                    continue
                rows = []
                spec_data = section.get('data')

                if isinstance(spec_data, dict):
                    # Новый формат: {группа: {подпись: значение}}
                    for group_fields in spec_data.values():
                        if not isinstance(group_fields, dict):
                            continue
                        for label, value in group_fields.items():
                            if label:
                                rows.append({
                                    'label': str(label),
                                    'value': '' if value is None else str(value),
                                })
                elif isinstance(spec_data, list):
                    # Старый формат: [{key, title, fields: [{label, value, unit}]}]
                    for group in spec_data:
                        if not isinstance(group, dict):
                            continue
                        for field in (group.get('fields') or []):
                            if not isinstance(field, dict):
                                continue
                            label = field.get('label') or field.get('key') or ''
                            value = field.get('value')
                            unit = field.get('unit')
                            text = '' if value is None else str(value)
                            if unit:
                                text = f'{text} {unit}'.strip()
                            if label:
                                rows.append({'label': str(label), 'value': text})

                if rows:
                    return rows
        except Exception:
            pass

    return [
        {'label': str(s.get('label', '')), 'value': str(s.get('value', ''))}
        for s in (fallback_specs or [])
        if s.get('label')
    ]


def build_context(cart):
    items_qs = (
        cart.items
        .select_related('sku', 'sku__equipment_type', 'sku__brand')
        .order_by('added_at', 'id')
    )

    items = []
    specs = []
    specs_seen = set()
    total = Decimal('0.00')

    for idx, item in enumerate(items_qs, start=1):
        serialized = CartItemSerializer(item).data
        summary = serialized.get('equipment_summary') or {}

        price = _to_decimal(serialized.get('price'))
        qty = int(item.quantity or 0)
        line_sum = price * qty
        total += line_sum

        article = summary.get('code') or item.sku.code or ''
        description = summary.get('name') or item.sku.name or ''

        items.append({
            'n': idx,
            'article': article,
            'description': description,
            'qty': qty,
            'price': _fmt_money(price),
            'sum': _fmt_money(line_sum),
        })

        if item.sku_id not in specs_seen:
            specs_seen.add(item.sku_id)
            specs.append({
                'article': article,
                'name': description,
                'rows': _extract_spec_rows(item.sku, summary.get('specs') or []),
            })

    project_customer_user = cart.employee
    project_customer = cart.project_customer
    if project_customer is None and project_customer_user is not None:
        project_customer = getattr(project_customer_user, 'customer', None)

    customer = ''
    if project_customer is not None:
        customer = getattr(project_customer, 'name', '') or ''

    return {
        'number': generate_quotation_number(project_customer, project_customer_user),
        'date': timezone.now().strftime('%d.%m.%Y'),
        'customer': customer,
        'cart_name': cart.name or '',
        'items': items,
        'total': _fmt_money(total),
        'specs': specs,
    }


def _append_table(doc, context):
    doc.add_paragraph()

    table = doc.add_table(rows=1, cols=len(TABLE_HEADERS))
    table.style = 'Table Grid'

    hdr = table.rows[0].cells
    for i, text in enumerate(TABLE_HEADERS):
        hdr[i].text = text
        for run in hdr[i].paragraphs[0].runs:
            run.bold = True

    for item in context['items']:
        row = table.add_row().cells
        row[0].text = str(item['n'])
        row[1].text = item['article']
        row[2].text = item['description']
        row[3].text = str(item['qty'])
        row[4].text = item['price']
        row[5].text = item['sum']

    # Строка «Итого»
    row = table.add_row().cells
    merged = row[0]
    for c in row[1:5]:
        merged = merged.merge(c)
    merged.text = 'Итого'
    merged.paragraphs[0].runs[0].bold = True

    total_cell = table.rows[-1].cells[5]
    total_cell.text = context['total']
    total_cell.paragraphs[0].runs[0].bold = True


def _append_specs(doc, context):
    specs = context['specs']
    if not specs:
        return

    doc.add_paragraph()
    doc.add_heading('Спецификации', level=1)

    for spec in specs:
        p = doc.add_paragraph()
        p.add_run(f"{spec['article']} — {spec['name']}").bold = True
        for row in spec['rows']:
            doc.add_paragraph(f"{row['label']}: {row['value']}")


def build_cart_quotation(cart) -> bytes:
    """Собрать КП из корзины и вернуть байты .docx."""
    context = build_context(cart)

    doc = DocxTemplate(str(TEMPLATE_PATH))
    doc.render(context)

    _append_table(doc, context)
    _append_specs(doc, context)

    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()
