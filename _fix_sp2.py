new_func = '''def get_safety_positions(model_line_id=None, model_line_item_id=None,
                         actuator_variety_id=None, active_only=True):
    """
    Получить опции положения безопасности — как в конструкторе:
    запрашиваем through-модель напрямую и берём safety_position.name/id.
    """
    from pneumatic_actuators.models import PneumaticActuatorModelLineItem
    from pneumatic_actuators.models.pa_options import PneumaticSafetyPositionOption
    from params.models import SafetyPositionOption

    if model_line_item_id:
        qs = PneumaticSafetyPositionOption.objects.filter(
            model_line_item_id=model_line_item_id
        ).select_related('safety_position')
    elif model_line_id:
        ids = PneumaticActuatorModelLineItem.objects.filter(
            model_line_id=model_line_id
        ).values_list('id', flat=True)
        if actuator_variety_id:
            ids = ids.filter(pneumatic_actuator_variety_id=actuator_variety_id)
        qs = PneumaticSafetyPositionOption.objects.filter(
            model_line_item_id__in=list(ids)
        ).select_related('safety_position')
    elif actuator_variety_id:
        ids = PneumaticActuatorModelLineItem.objects.filter(
            pneumatic_actuator_variety_id=actuator_variety_id
        ).values_list('id', flat=True)
        qs = PneumaticSafetyPositionOption.objects.filter(
            model_line_item_id__in=list(ids)
        ).select_related('safety_position')
    else:
        qs = SafetyPositionOption.objects.all()
        if active_only:
            qs = qs.filter(is_active=True)
        return [{'id': obj.id, 'name': obj.name, 'code': obj.code} for obj in qs]

    if active_only:
        qs = qs.filter(is_active=True)

    # Deduplicate by safety_position.id
    seen = set()
    result = []
    for opt in qs:
        sp_id = opt.safety_position_id
        if sp_id not in seen:
            seen.add(sp_id)
            result.append({
                'id': sp_id,
                'name': opt.safety_position.name,
                'code': opt.safety_position.code,
                'encoding': opt.encoding,
            })
    return result


def get_filtered_model_line_items'''

target = r'pneumatic_actuators\actuator_selector_handler.py'
with open(target, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the old function
# Functions are: get_safety_positions (starts) ... get_filtered_model_line_items (starts after)
old_start = 'def get_safety_positions('
new_start = 'def get_filtered_model_line_items('

idx1 = content.find(old_start)
idx2 = content.find(new_start)

if idx1 >= 0 and idx2 > idx1:
    content = content[:idx1] + new_func + content[idx2 + len(new_start):]
    with open(target, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Replaced: {idx2 - idx1} chars')
else:
    print(f'Not found: start={idx1}, end={idx2}')
