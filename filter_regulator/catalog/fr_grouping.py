# filter_regulator/catalog/fr_grouping.py
"""Группировка карточек ФР по корпусу → сетка с чипсами (как у ПП)."""

from collections import OrderedDict

# Ключ template_vars → подпись чипса. Это опции, которые могут различаться
# внутри одного корпуса (остальное — от корпуса/серии).
CHIP_FIELDS = (
    ('filter_variety', 'Тип'),
    ('body_material', 'Материал корпуса'),
    ('ip', 'IP'),
    ('filtration_rating', 'Тонкость, мкм'),
    ('filter_element_material', 'Фильтр. элемент'),
    ('wall_mounting_included', 'Крепление'),
    ('has_shut_off_valve', 'Отсечной клапан'),
    ('pressure_range', 'Давление'),
)


def group_by_body(cards):
    """Сгруппировать сериализованные карточки ФР по body_id.

    ``cards`` — список dict из ``to_values_dict`` + поля ``body_id``.
    Возвращает список групп:
        [{body_id, chips: [{key, label, variants: [{value, label}]}], items: [...]}].
    Каждый item дополняется ``sku_id`` и ``options`` (ключ → {value}).
    """
    groups = OrderedDict()
    for card in cards:
        body_id = card.get('body_id')
        group = groups.setdefault(body_id, {'body_id': body_id, 'items': []})

        tv = card.get('template_vars') or {}
        options = {key: {'value': str(tv.get(key) or '')} for key, _ in CHIP_FIELDS}
        card['sku_id'] = (card.get('sku') or {}).get('id')
        card['options'] = options
        group['items'].append(card)

    result = []
    for group in groups.values():
        chips = []
        for key, label in CHIP_FIELDS:
            variants = []
            seen = set()
            for item in group['items']:
                value = item['options'].get(key, {}).get('value', '')
                if value in seen:
                    continue
                seen.add(value)
                variants.append({'value': value, 'label': value})
            if len(variants) > 1:
                chips.append({'key': key, 'label': label, 'variants': variants})
        group['chips'] = chips
        result.append(group)

    return result
