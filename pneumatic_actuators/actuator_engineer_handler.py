# pneumatic_actuators/actuator_selector_handler.py

import logging
from typing import Dict, Any, Tuple, Optional, List

from params.models import IpOption, HandWheelInstalledOption, StemShapes, \
    PneumaticAirSupplyPressure
from params.exd_models import ExdOption
from pneumatic_actuators.models import BodyThrustTorqueTable, PneumaticActuatorVariety, \
    PneumaticActuatorConstructionVariety
from core.utils.localization import localized_name, pick_i18n

logger = logging.getLogger(__name__)


def get_actuator_options(model_line_id: Optional[int] = None ,
                         model_line_item_id: Optional[int] = None ,
                         actuator_variety_id: Optional[int] = None ,
                         locale: Optional[str] = None) -> Dict[str , Any] :
    """
    Возвращает все доступные опции для привода на основе выбранных параметров

    Args:
        model_line_id: ID выбранной серии моделей
        model_line_item_id: ID выбранной модели в серии
        actuator_variety_id: ID выбранного вида привода (DA/SR)
        locale: локаль данных (ru/en/cn) для локализации названий опций

    Returns:
        Dict: словарь со всеми опциями
    """
    result = {
        'actuator_varieties' : [] ,
        'safety_positions' : [] ,
        'temperature_options' : [] ,
        'ip_options' : [] ,
        'exd_options' : [] ,
        'coating_options' : [] ,
        'manual_override_options' : []
    }

    # 1. Виды приводов (DA/SR) - не зависят от model_line
    result['actuator_varieties'] = PneumaticActuatorVariety.get_for_select(active_only=True , locale=locale)

    # 2. Положения безопасности — требования (реальные опции params.SafetyPositionOption),
    # а не through-строки серии: id идёт в create-sku и должен быть ID реальной опции.
    # Правило DA/SR (на бэке, не на фронте):
    #   DA → только «Оставаться в текущем положении» (code='fl');
    #   SR → «НО»/«НЗ» (code='no'/'nc');
    #   вид не выбран → все активные.
    from params.models import SafetyPositionOption
    safety_qs = SafetyPositionOption.objects.filter(is_active=True).order_by('sorting_order')
    if actuator_variety_id:
        variety = PneumaticActuatorVariety.objects.filter(id=actuator_variety_id).first()
        variety_code = variety.code if variety else None
        if variety_code == 'DA':
            safety_qs = safety_qs.filter(code='fl')
        elif variety_code == 'SR':
            safety_qs = safety_qs.filter(code__in=('no', 'nc'))
    result['safety_positions'] = [
        {'id' : o.id , 'name' : localized_name(o , locale) , 'code' : o.code}
        for o in safety_qs
    ]

    # 3. IP, Exd, ручной дублер — мастер-справочники (требования):
    # exd используется в фильтре подбора (нужны ID видов params.ExdOption),
    # а ip/manual_override — в create-sku (нужны ID реальных опций).
    option_classes = {
        'ip_options' : IpOption ,
        'exd_options' : ExdOption ,
        'manual_override_options' : HandWheelInstalledOption
    }
    for key , option_class in option_classes.items() :
        result[key] = option_class.get_for_select(active_only=True , locale=locale)

    # Материал корпуса и покрытие корпуса — РАЗДЕЛЬНЫЕ ключи в модели
    # (body_material FK + body_coating_option FK), поэтому и селекторы раздельные:
    #   body_material_options — уникальные материалы (MaterialGeneral);
    #   coating_options       — уникальные покрытия (BodyCoatingOption, источник истины).
    from pneumatic_actuators.models.pa_options import PneumaticBodyDesignOption
    from materials.models import MaterialGeneral
    from params.models import BodyCoatingOption

    bd_qs = PneumaticBodyDesignOption.objects.filter(is_active=True)
    if model_line_id :
        bd_qs = bd_qs.filter(model_line_id=model_line_id)

    material_ids = bd_qs.values_list('body_material_id' , flat=True).distinct()
    result['body_material_options'] = [
        {'id' : m.id , 'name' : localized_name(m , locale) , 'code' : m.code or ''}
        for m in MaterialGeneral.objects.filter(id__in=material_ids , is_active=True).order_by('name')
    ]

    coating_ids = bd_qs.exclude(body_coating_option__isnull=True).values_list(
        'body_coating_option_id' , flat=True
    ).distinct()
    result['coating_options'] = [
        {'id' : c.id , 'name' : localized_name(c , locale) , 'code' : c.code or ''}
        for c in BodyCoatingOption.objects.filter(id__in=coating_ids , is_active=True).order_by('sorting_order')
    ]

    # Температура окружающей среды: уникальные нижние границы work_temp_min,
    # близкие значения объединяем (шаг 10°C, оставляем более холодную).
    from pneumatic_actuators.models.pa_options import PneumaticTemperatureOption
    temp_qs = PneumaticTemperatureOption.objects.filter(
        is_active=True , work_temp_min__isnull=False
    )
    if model_line_id :
        temp_qs = temp_qs.filter(model_line_id=model_line_id)
    temp_vals = sorted(set(temp_qs.values_list('work_temp_min' , flat=True)))  # от холодной к тёплой
    merged = []
    for v in temp_vals :
        if not merged or abs(v - merged[-1]) > 10 :
            merged.append(v)
    merged.sort(reverse=True)  # от тёплой к холодной (для UI)
    result['temperature_options'] = [
        {'id' : v , 'name' : f'{v}°C' , 'code' : str(v)} for v in merged
    ]

    return result

def get_safety_positions(model_line_id: Optional[int] = None ,
                         model_line_item_id: Optional[int] = None ,
                         actuator_variety_id: Optional[int] = None ,
                         active_only: bool = True) -> List[Dict] :
    """
    Получить опции положения безопасности с учетом всех параметров

    Логика отбора:
    1. Если есть model_line_item_id - берем опции для конкретной модели
    2. Если есть model_line_id - берем опции для всех моделей в серии
       (с учетом actuator_variety_id, если указан)
    3. Если есть actuator_variety_id - берем опции для всех моделей с таким видом привода
    4. Если ничего нет - берем базовые опции из params.SafetyPositionOption
    """
    from pneumatic_actuators.models import PneumaticActuatorModelLineItem
    from pneumatic_actuators.models.pa_options import PneumaticSafetyPositionOption
    from params.models import SafetyPositionOption

    # Приоритет: model_line_item_id > model_line_id > actuator_variety_id > базовые опции

    # Вариант 1: конкретная модель
    if model_line_item_id :
        logger.debug(f"Getting safety positions for model_line_item_id={model_line_item_id}")
        return PneumaticSafetyPositionOption.get_for_select(
            model_line_item_id=model_line_item_id ,
            active_only=active_only
        )

    # Вариант 2: серия моделей
    if model_line_id :
        logger.debug(f"Getting safety positions for model_line_id={model_line_id}")

        # Если указан вид привода, сначала фильтруем модели
        if actuator_variety_id :
            logger.debug(f"Filtering by actuator_variety_id={actuator_variety_id}")
            # Получаем model_line_item_id для данной серии и вида привода
            model_line_item_ids = PneumaticActuatorModelLineItem.objects.filter(
                model_line_id=model_line_id ,
                pneumatic_actuator_variety_id=actuator_variety_id
            ).values_list('id' , flat=True)

            if not model_line_item_ids :
                logger.warning(
                    f"No model line items found for model_line_id={model_line_id}, actuator_variety_id={actuator_variety_id}")
                return []

            return PneumaticSafetyPositionOption.get_for_select(
                model_line_item_ids=list(model_line_item_ids) ,
                active_only=active_only
            )

        # Без фильтрации по виду привода
        return PneumaticSafetyPositionOption.get_for_select(
            model_line_id=model_line_id ,
            active_only=active_only
        )

    # Вариант 3: только вид привода (без серии)
    if actuator_variety_id :
        logger.debug(f"Getting safety positions for actuator_variety_id={actuator_variety_id}")

        model_line_item_ids = PneumaticActuatorModelLineItem.objects.filter(
            pneumatic_actuator_variety_id=actuator_variety_id
        ).values_list('id' , flat=True)

        if not model_line_item_ids :
            logger.warning(f"No model line items found for actuator_variety_id={actuator_variety_id}")
            return []

        return PneumaticSafetyPositionOption.get_for_select(
            model_line_item_ids=list(model_line_item_ids) ,
            active_only=active_only
        )

    # Вариант 4: базовые опции
    logger.debug("Getting base safety positions from params.SafetyPositionOption")
    queryset = SafetyPositionOption.objects.all()
    if active_only :
        queryset = queryset.filter(is_active=True)

    return [{'id' : obj.id , 'name' : obj.name , 'code' : obj.code} for obj in queryset]


def get_filtered_model_line_items(model_line_id: Optional[int] = None,
                                  actuator_variety_id: Optional[int] = None) -> List[Dict]:
    """
    Возвращает список моделей в серии с фильтрацией по виду привода

    Args:
        model_line_id: ID серии моделей
        actuator_variety_id: ID вида привода (DA или SR)

    Returns:
        List[Dict]: список моделей
    """
    from pneumatic_actuators.models import PneumaticActuatorModelLineItem

    return PneumaticActuatorModelLineItem.get_for_select(
        model_line_id=model_line_id,
        actuator_variety_id=actuator_variety_id,
        active_only=True
    )

# ── Названия селекторов (UI-подписи) — локализуются на бэке, чтобы фронт
#    не держал свой словарь для этих подписей. Ключ — код селектора. ──
SELECTOR_LABELS_I18N = {
    'valve_type': {'ru': 'Тип арматуры', 'en': 'Valve type', 'cn': '阀门类型'},
    'dn': {'ru': 'DN', 'en': 'DN', 'cn': 'DN'},
    'pn': {'ru': 'PN', 'en': 'PN', 'cn': 'PN'},
    'mounting_plate': {'ru': 'Монтажная площадка', 'en': 'Mounting flange', 'cn': '安装法兰'},
    'stem_shape': {'ru': 'Форма штока', 'en': 'Stem shape', 'cn': '阀杆形状'},
    'stem': {'ru': 'Шток', 'en': 'Stem', 'cn': '阀杆'},
    'torque_without_safety': {'ru': 'Момент без запаса (Нм)', 'en': 'Torque, no safety factor (Nm)', 'cn': '扭矩（无安全系数，Nm）'},
    'safety_factor': {'ru': 'Коэффициент запаса', 'en': 'Safety factor', 'cn': '安全系数'},
    'torque_with_safety': {'ru': 'Момент с запасом (Нм)', 'en': 'Torque with safety factor (Nm)', 'cn': '扭矩（含安全系数，Nm）'},
    'model_line': {'ru': 'Серия моделей', 'en': 'Model series', 'cn': '型号系列'},
    'actuator_variety': {'ru': 'Тип привода (DA/SR)', 'en': 'Actuator type (DA/SR)', 'cn': '执行器类型（DA/SR）'},
    'safety_position': {'ru': 'Положение безопасности', 'en': 'Fail-safe position', 'cn': '安全位置'},
    'air_pressure': {'ru': 'Давление в пневмосистеме, бар', 'en': 'Supply pressure, bar', 'cn': '供气压力, bar'},
    'ip': {'ru': 'IP защита', 'en': 'IP rating', 'cn': 'IP防护'},
    'exd': {'ru': 'Взрывозащита', 'en': 'Explosion protection', 'cn': '防爆'},
    'coating': {'ru': 'Покрытие корпуса', 'en': 'Body coating', 'cn': '壳体涂层'},
    'body_material': {'ru': 'Материал корпуса', 'en': 'Body material', 'cn': '壳体材料'},
    'manual_override': {'ru': 'Ручной дублёр', 'en': 'Manual override', 'cn': '手动操作'},
    'temp_min': {'ru': 'Температура мин. (°C)', 'en': 'Temp. min (°C)', 'cn': '最低温度（°C）'},
    'temp_max': {'ru': 'Температура макс. (°C)', 'en': 'Temp. max (°C)', 'cn': '最高温度（°C）'},
}


def _get_selector_labels(locale=None) -> Dict[str, str]:
    """Локализованные подписи селекторов для текущей локали (ru — базовый)."""
    from core.utils.localization import DEFAULT_LOCALE
    locale = locale or DEFAULT_LOCALE
    out = {}
    for key, i18n in SELECTOR_LABELS_I18N.items():
        out[key] = i18n.get(locale) or i18n.get('ru') or key
    return out


def get_initial_data(locale=None, fields=None) -> Dict[str, Any]:
    """
    Возвращает начальные данные для загрузки страницы.

    ``fields`` (опционально) — итерабельное с именами ключей; если задано,
    выполняются только запросы для этих ключей (лёгкий частичный ответ).
    """
    from pneumatic_actuators.models import PneumaticActuatorModelLine
    from params.models import DnVariety, PnVariety, MountingPlateTypes, StemSize, ValveTypes

    if fields is not None:
        fields = set(fields)
    want = (lambda key: fields is None or key in fields)

    data: Dict[str, Any] = {}
    if want('model_lines'):
        data['model_lines'] = PneumaticActuatorModelLine.get_for_select(active_only=True)
    if want('actuator_varieties'):
        data['actuator_varieties'] = PneumaticActuatorVariety.get_for_select(active_only=True, locale=locale)
    if want('construction_varieties'):
        data['construction_varieties'] = PneumaticActuatorConstructionVariety.get_for_select(active_only=True, locale=locale)
    if want('dn_varieties'):
        data['dn_varieties'] = DnVariety.get_for_select(active_only=True, locale=locale)
    if want('pn_varieties'):
        data['pn_varieties'] = PnVariety.get_for_select(active_only=True, locale=locale)
    if want('air_pressure'):
        # Только давления, по которым реально есть строки в таблице моментов
        # (SPRING и давления без строк — исключаем).
        torque_pressure_ids = set(
            BodyThrustTorqueTable.objects.filter(pressure__isnull=False)
            .values_list('pressure_id', flat=True).distinct()
        )
        data['air_pressure'] = [
            p for p in PneumaticAirSupplyPressure.get_for_select(active_only=True, locale=locale)
            if p.get('code') != 'spring' and p.get('id') in torque_pressure_ids
        ]
    if want('mounting_plates'):
        data['mounting_plates'] = MountingPlateTypes.get_for_select(active_only=True, locale=locale)
    if want('stem_shapes'):
        data['stem_shapes'] = StemShapes.get_for_select(active_only=True, locale=locale)
    if want('stem_sizes'):
        data['stem_sizes'] = StemSize.get_for_select(active_only=True, locale=locale)
    if want('valve_types'):
        data['valve_types'] = ValveTypes.get_for_select(active_only=True, locale=locale)
    if want('labels'):
        data['labels'] = _get_selector_labels(locale)
    return data


def _normalize_selection_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Приводит параметры подбора к внутреннему контракту (2026-09-01):
    - torque_with_safety = torque_without_safety * safety_factor (если явный не задан);
    - air_pressure_id: по умолчанию 13 (6 бар);
    - actuator_variety_code: из code или из id; по умолчанию 'DA'.
    Принимает как формат фронтенда (torque_without_safety + safety_factor),
    так и legacy-формат (готовый torque_with_safety).
    """
    p = dict(params)

    if not p.get('torque_with_safety'):
        try:
            tws = float(p.get('torque_without_safety') or 0)
            sf = float(p.get('safety_factor') or 0)
        except (TypeError, ValueError):
            tws = sf = 0
        p['torque_with_safety'] = tws * sf

    if not p.get('air_pressure_id'):
        p['air_pressure_id'] = 13  # 6 бар по умолчанию

    if not p.get('actuator_variety_code'):
        if p.get('actuator_variety_id'):
            from pneumatic_actuators.models import PneumaticActuatorVariety
            variety = PneumaticActuatorVariety.objects.filter(id=p['actuator_variety_id']).first()
            p['actuator_variety_code'] = variety.code if variety else 'DA'
        else:
            p['actuator_variety_code'] = 'DA'

    return p


def validate_selection_params(params: Dict[str , Any]) -> Tuple[bool , Optional[str] , Optional[str] , List[str]] :
    """
    Валидация параметров подбора привода

    Args:
        params: словарь с параметрами

    Returns:
        Tuple[bool, Optional[str], Optional[str], List[str]]:
            - is_valid: результат валидации
            - error_field: имя поля с ошибкой
            - error_message: сообщение об ошибке
            - error_fields: список всех полей с ошибками
    """
    errors = []
    error_fields = []

    # 1. Тип арматуры — необязателен: в поиске find_suitable_actuators() не используется
    #    (оставлен в контракте для совместимости с PaSelectionPage).

    # 2. Проверка момента с запасом (нормализован из torque_without_safety * safety_factor)
    try:
        torque_with_safety = float(params.get('torque_with_safety') or 0)
    except (TypeError, ValueError):
        torque_with_safety = 0
    if not torque_with_safety or torque_with_safety <= 0 :
        errors.append("Не указан момент с запасом (нужны torque_with_safety или torque_without_safety + safety_factor)")
        error_fields.append('torque_with_safety')

    # 2A. Проверка управляющего давления (нормализовано: по умолчанию 6 бар)
    if not params.get('air_pressure_id') or params.get('air_pressure_id') == 0:
        errors.append("Не указано давление в пневмосистеме")
        error_fields.append('air_pressure_id')

    # 3. Проверка типа привода DA/SR (code или id — нормализовано)
    actuator_variety_code = params.get('actuator_variety_code')
    if not actuator_variety_code:
        errors.append("Не выбран тип привода (DA/SR)")
        error_fields.append('actuator_variety_code')

    # 4. Если привод SR - проверка положения безопасности
    actuator_variety_code = params.get('actuator_variety_code')
    safety_position_id = params.get('safety_position_id')

    if actuator_variety_code == 'SR' :
        if not safety_position_id or safety_position_id == 0 :
            errors.append("Для привода SR обязательно выбор положения безопасности (NO/NC)")
            error_fields.append('safety_position_id')

    if errors :
        return False , error_fields[0] if error_fields else None , errors[0] , error_fields

    return True , None , None , []

# def find_apppropriate_model_line(params: Dict[str , Any]) -> Dict[str , Any] :

def _match_exd_for_model_lines(search_results: List[Dict], exd_value, exd_exact_id=None) -> List[Dict]:
    """Фильтрует серии по взрывозащите: семантика «не хуже чем».

    Принимает (формат компонента ExdFilter):
      - None / '' / [] — фильтр не задан;
      - '_none_'  — «общепром» (только серии без конкретных видов Ex);
      - '_empty_' — нет совместимых видов (пустой результат);
      - одиночный id / список id / csv-строка id — виды params.ExdOption.

    ``exd_exact_id`` — точный запрошенный вид (для exact/compatible-разделения).
    Каждая совпавшая серия аннотируется ``exd_exact`` (True — в выбранной строке
    есть точный вид; для «общепром» — отсутствие Ex и есть точное совпадение).
    """
    from pneumatic_actuators.models.pa_options import PneumaticExdOption

    if exd_value in (None, '', []):
        return search_results

    if exd_value == '_none_':
        compat_ids: set = set()
        is_common = True
    elif exd_value == '_empty_':
        return []
    elif isinstance(exd_value, str) and ',' in exd_value:
        compat_ids = {int(v) for v in exd_value.split(',') if v.strip()}
        is_common = False
    elif isinstance(exd_value, (list, tuple, set)):
        compat_ids = {int(v) for v in exd_value}
        is_common = False
    else:
        # Одиночный id (старый селектор): расширяем до совместимых видов.
        try:
            single = int(exd_value)
            requested = ExdOption.objects.filter(id=single).first()
            compat_ids = requested.get_compatible_ids() if requested else {single}
        except (ValueError, TypeError):
            compat_ids = set()
        is_common = False

    # Точный запрошенный вид (для exact/compatible). Если exact_id не передан,
    # а значение — одиночный id (старый селектор) — считаем точным сам id.
    exact_int = None
    if exd_exact_id not in (None, ''):
        try:
            exact_int = int(exd_exact_id)
        except (ValueError, TypeError):
            exact_int = None
    elif not is_common:
        try:
            v = exd_value
            if isinstance(v, str) and ',' not in v:
                exact_int = int(v)
            elif isinstance(v, (int, float)):
                exact_int = int(v)
        except (ValueError, TypeError):
            exact_int = None

    rows_by_line: Dict[int, list] = {}
    for row in PneumaticExdOption.objects.filter(is_active=True).prefetch_related('exd_options'):
        rows_by_line.setdefault(row.model_line_id, []).append(row)

    result = []
    for ml in search_results:
        ml_id = ml.get('model_line_id')
        best = None
        common_row = None
        for row in rows_by_line.get(ml_id, []):
            variety_ids = {o.id for o in row.exd_options.all()}
            if not variety_ids:
                # Пустой M2M = «общепром» (fallback только под запрос «общепром»).
                if common_row is None:
                    common_row = row
                continue
            if variety_ids & compat_ids:
                best = row
                break
        if best is None and is_common:
            best = common_row
        if best is None:
            continue  # серия не поддерживает запрошенную взрывозащиту
        variety_ids = [o.id for o in best.exd_options.all()]
        ml['exd_option_id'] = best.id
        ml['exd_encoding'] = best.encoding or ''
        ml['exd_short'] = best.get_exd_short_list or ''
        ml['exd_variety_ids'] = variety_ids
        ml['exd_matched'] = True
        # exact: точный вид есть в выбранной строке; для «общепром» — отсутствие Ex.
        ml['exd_exact'] = is_common or (exact_int is not None and exact_int in set(variety_ids))
        result.append(ml)
    return result


def _dedup_series_by_body(search_results: List[Dict]) -> List[Dict]:
    """Для каждого body оставляет только одну серию.

    Приоритет — серия без конкретной взрывозащиты (общепром), затем по sorting_order.
    Вызывается ПОСЛЕ exd-фильтра: если exd обязателен, серии без exd уже отсеяны.
    """
    from collections import defaultdict

    specific_ml_ids = BodyThrustTorqueTable._get_specific_exd_series(
        {ml.get('model_line_id') for ml in search_results}
    )

    body_to_mls = defaultdict(list)
    for ml in search_results :
        for item in ml.get('model_line_items' , []) :
            body_to_mls[item['body_id']].append(ml)

    keep_ml_by_body = {}
    for body_id, mls in body_to_mls.items() :
        if len(mls) == 1 :
            keep_ml_by_body[body_id] = mls[0]['model_line_id']
        else :
            mls.sort(key=lambda m : (
                m['model_line_id'] in specific_ml_ids ,
                m.get('model_line_sorting_order' , 999)
            ))
            keep_ml_by_body[body_id] = mls[0]['model_line_id']

    for ml in search_results :
        ml['model_line_items'] = [
            it for it in ml.get('model_line_items' , [])
            if keep_ml_by_body.get(it['body_id']) == ml['model_line_id']
        ]

    return [ml for ml in search_results if ml.get('model_line_items')]


# ── Измерения опций для группировки карточек по model_line_item (чипсы) ──
_OPTION_DIMENSION_LABELS = {
    'temperature': {'ru': 'Температура', 'en': 'Temperature', 'cn': '温度'},
    'coating': {'ru': 'Покрытие корпуса', 'en': 'Body coating', 'cn': '壳体涂层'},
    'exd': {'ru': 'Взрывозащита', 'en': 'Explosion protection', 'cn': '防爆'},
    'ip': {'ru': 'IP', 'en': 'IP', 'cn': 'IP'},
    'manual_override': {'ru': 'Ручной дублёр', 'en': 'Manual override', 'cn': '手动操作'},
    'safety_position': {'ru': 'Положение безопасности', 'en': 'Fail-safe position', 'cn': '安全位置'},
}


def _dimension_label(key, locale):
    from core.utils.localization import DEFAULT_LOCALE
    locale = locale or DEFAULT_LOCALE
    i18n = _OPTION_DIMENSION_LABELS.get(key, {})
    return i18n.get(locale) or i18n.get('ru') or key


def _card_option_values(card_item, locale):
    """Плоский словарь значений опций карточки (для чипсов групповой карточки).

    Подписи — чистые значения без суффиксов «(Стандарт)»/«(Опция)» и без
    encoding-префиксов: для чипса важно ЧЕМ варианты различаются, а не кодировка.
    """
    out = {}

    t = card_item.selected_temperature
    if t is not None:
        out['temperature'] = {
            'value': str(t.id),
            'label': f"{t.work_temp_min}…{t.work_temp_max}°C",
        }

    coat = card_item.selected_body_coating
    if coat is not None:
        parts = []
        if coat.body_material:
            parts.append(localized_name(coat.body_material, locale))
        if coat.body_coating_option:
            parts.append(localized_name(coat.body_coating_option, locale))
        elif coat.body_coating:
            parts.append(pick_i18n(coat.body_coating, locale) or '')
        label = ', '.join(p for p in parts if p)
        if label:
            out['coating'] = {'value': str(coat.id), 'label': label}

    exd = card_item.selected_exd
    if exd is not None:
        label = card_item._res_exd_short() or exd.encoding or ''
        if label:
            out['exd'] = {'value': str(exd.id), 'label': label}

    ip = card_item.selected_ip
    if ip is not None:
        out['ip'] = {'value': str(ip.id), 'label': localized_name(ip, locale) or str(ip)}

    mo = card_item.selected_manual_override
    if mo is not None:
        out['manual_override'] = {'value': str(mo.id), 'label': localized_name(mo, locale) or str(mo)}

    sp = card_item.selected_safety_position
    if sp is not None:
        out['safety_position'] = {'value': str(sp.id), 'label': localized_name(sp, locale) or str(sp)}

    return out


def _group_cards_by_model_line_item(cards, locale):
    """Группирует карточки по model_line_item; вычисляет чипсы различающихся опций."""
    from collections import OrderedDict

    groups = OrderedDict()
    for card in cards:
        key = card.get('model_line_item_id') or ('body', card.get('body_id'))
        groups.setdefault(key, []).append(card)

    result = []
    for _key, items in groups.items():
        first = items[0]
        group = {
            'model_line_item_id': first.get('model_line_item_id'),
            'body_id': first.get('body_id'),
            'code': first.get('code'),
            'name': first.get('name'),
            'title': first.get('title'),
            'list_title': first.get('list_title'),
            'images': first.get('images'),
            'sku': first.get('sku'),
            'sku_id': first.get('sku_id'),
            'is_exact': first.get('is_exact'),
            'items': items,
            'chips': [],
        }

        for dim in ('temperature', 'coating', 'exd', 'ip', 'manual_override', 'safety_position'):
            variants = []
            seen = set()
            for card in items:
                opt = card.get('options', {}).get(dim)
                if not opt or opt['value'] in seen:
                    continue
                seen.add(opt['value'])
                variants.append({'value': opt['value'], 'label': opt['label'], 'sku_id': card.get('sku_id')})
            if len(variants) > 1:
                group['chips'].append({
                    'key': dim,
                    'label': _dimension_label(dim, locale),
                    'variants': variants,
                })

        result.append(group)

    return result


def _search_catalog_items(params: Dict[str, Any], locale: Optional[str] = None) -> Dict[str, Any]:
    """Подбор ПП: тела по моменту (со скорингом) → exd/температура/конструкция
    (по сериям, как в старой версии) → материализованные карточки (SKU) найденных тел."""
    from pneumatic_actuators.models import PneumaticActuatorCatalogItem
    from pneumatic_actuators.models import PneumaticActuatorModelLine

    actuator_variety_code = params.get('actuator_variety_code', 'DA')
    torque_with_safety = float(params.get('torque_with_safety', 0))
    work_pressure_id = params.get('air_pressure_id')
    model_line_id = params.get('model_line_id')

    # 1. Тела по моменту/давлению/виду (со скором и запасом по моменту).
    body_ids = None
    if model_line_id:
        from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLineItem
        body_ids = list(PneumaticActuatorModelLineItem.objects.filter(
            model_line_id=model_line_id, is_active=True).values_list('body_id', flat=True).distinct())
    found = BodyThrustTorqueTable.find_suitable_actuators(
        torque_with_sf=torque_with_safety,
        work_pressure_id=work_pressure_id,
        actuator_variety=actuator_variety_code,
        body_ids=body_ids,
        model_line_id=model_line_id,
        max_bodies_per_series=2,
    )

    # 2. Exd — по сериям (совместимые виды + exact), как раньше.
    exd_id = params.get('exd_id')
    if exd_id:
        found = _match_exd_for_model_lines(found, exd_id, exd_exact_id=params.get('exd_id_exact'))

    # 3. Конструкция — по серии.
    construction_variety_id = params.get('construction_variety_id')
    if construction_variety_id:
        allowed = set(PneumaticActuatorModelLine.objects.filter(
            pneumatic_actuator_construction_variety_id=construction_variety_id, is_active=True
        ).values_list('id', flat=True))
        found = [ml for ml in found if ml.get('model_line_id') in allowed]

    # 4. Материал корпуса и покрытие корпуса — раздельные фильтры по серии
    #    (body_design_options__body_material / __body_coating_option).
    body_material_id = params.get('body_material_id')
    if body_material_id :
        allowed = set(PneumaticActuatorModelLine.objects.filter(
            body_design_options__body_material_id=body_material_id , is_active=True
        ).values_list('id' , flat=True).distinct())
        found = [ml for ml in found if ml.get('model_line_id') in allowed]

    coating_id = params.get('coating_id')
    if coating_id :
        allowed = set(PneumaticActuatorModelLine.objects.filter(
            body_design_options__body_coating_option_id=coating_id , is_active=True
        ).values_list('id' , flat=True).distinct())
        found = [ml for ml in found if ml.get('model_line_id') in allowed]

    # 5. Температура — по серии (покрывает диапазон; exact — точное совпадение).
    temp_min = params.get('temp_min')
    temp_max = params.get('temp_max')
    temp_exact_ml_ids = set()
    if temp_min or temp_max:
        try:
            temp_min = float(temp_min) if temp_min not in (None, '') else None
        except (TypeError, ValueError):
            temp_min = None
        try:
            temp_max = float(temp_max) if temp_max not in (None, '') else None
        except (TypeError, ValueError):
            temp_max = None
        tq = PneumaticActuatorModelLine.objects.filter(is_active=True)
        if temp_min is not None:
            tq = tq.filter(temperature_options__work_temp_min__lte=temp_min)
        if temp_max is not None:
            tq = tq.filter(temperature_options__work_temp_max__gte=temp_max)
        allowed = set(tq.values_list('id', flat=True).distinct())
        found = [ml for ml in found if ml.get('model_line_id') in allowed]
        from pneumatic_actuators.models.pa_options import PneumaticTemperatureOption
        eq = PneumaticTemperatureOption.objects.filter(is_active=True)
        if temp_min is not None:
            eq = eq.filter(work_temp_min=temp_min)
        if temp_max is not None:
            eq = eq.filter(work_temp_max=temp_max)
        temp_exact_ml_ids = set(eq.values_list('model_line_id', flat=True).distinct())

    # 6. Дедуп одинаковых корпусов между сериями.
    found = _dedup_series_by_body(found)

    # 7. exact/compatible — по серии (exd + температура).
    exd_active = bool(params.get('exd_id'))
    temp_active = bool(params.get('temp_min') or params.get('temp_max'))
    for ml in found:
        exd_exact = ml.get('exd_exact', False) if exd_active else True
        temp_exact = (ml.get('model_line_id') in temp_exact_ml_ids) if temp_active else True
        ml['is_exact'] = bool(exd_exact and temp_exact)

    # 8. Карточки (SKU) для найденных тел (лёгкая сериализация, без to_dict).
    safety_position_id = params.get('safety_position_id')
    cards = []
    for ml in found:
        for item in ml.get('model_line_items', []):
            qs = PneumaticActuatorCatalogItem.objects.filter(
                is_active=True,
                body_id=item.get('body_id'),
                pneumatic_actuator_variety__code=actuator_variety_code,
            )
            if actuator_variety_code == 'SR' and item.get('spring_qty_id'):
                qs = qs.filter(selected_springs_qty_id=item.get('spring_qty_id'))
            if safety_position_id:
                qs = qs.filter(selected_safety_position_id=safety_position_id)
            # Карточка должна соответствовать выбранному материалу/покрытию корпуса
            # (источник истины — selected_body_coating, а не серия: у серии может быть
            # несколько исполнений корпуса, а карточка материализует одно).
            if body_material_id:
                qs = qs.filter(selected_body_coating__body_material_id=body_material_id)
            if coating_id:
                qs = qs.filter(selected_body_coating__body_coating_option_id=coating_id)
            # Карточки должны соответствовать выбранному exd и покрывать температуру.
            if exd_id and ml.get('exd_option_id'):
                qs = qs.filter(selected_exd_id=ml.get('exd_option_id'))
            if temp_active:
                if temp_min is not None:
                    qs = qs.filter(selected_temperature__work_temp_min__lte=temp_min)
                if temp_max is not None:
                    qs = qs.filter(selected_temperature__work_temp_max__gte=temp_max)
            qs = (qs
                .select_related(
                    'model_line', 'body', 'sku', 'image_gallery', 'model_line__image_gallery',
                    'pneumatic_actuator_variety',
                    'selected_temperature', 'selected_exd', 'selected_body_coating',
                    'selected_body_coating__body_material',
                    'selected_body_coating__body_coating_option',
                    'selected_ip', 'selected_manual_override', 'selected_safety_position',
                )
                .prefetch_related(
                    'image_gallery__items__image__variants',
                    'model_line__image_gallery__items__image__variants',
                    'selected_exd__exd_options',
                    'selected_exd__exd_options__explosion_protection_class',
                )
                .distinct())
            for card_item in qs:
                try:
                    list_params = card_item._get_list_params(locale=locale)
                except Exception:
                    list_params = []
                try:
                    list_title = card_item.generate_list_title(locale) or card_item.name or ''
                except Exception:
                    list_title = card_item.name or ''
                cards.append({
                    'id': card_item.id,
                    'model_line_item_id': card_item.source_model_line_item_id,
                    'body_id': card_item.body_id,
                    'code': card_item.code or '',
                    'name': card_item.name or '',
                    'title': card_item.name or '',
                    'list_title': list_title,
                    'list_params': list_params,
                    'images': card_item._get_list_preview_images(),
                    'sku': {'id': card_item.sku_id, 'code': card_item.sku.code, 'name': card_item.sku.name} if card_item.sku_id else None,
                    'sku_id': card_item.sku_id,
                    'is_exact': bool(ml.get('is_exact')),
                    'score': item.get('score', 0),
                    'options': _card_option_values(card_item, locale),
                })

    # Сортировка по точности момента (чем меньше score, тем ближе к требуемому).
    cards.sort(key=lambda c: c.get('score', 999))
    for c in cards:
        c.pop('score', None)

    groups = _group_cards_by_model_line_item(cards, locale)
    return {
        'search_results': groups,
        'total_found': len(groups),
        'total_items': len(cards),
    }


def process_selection_params(params: Dict[str , Any], locale: Optional[str] = None) -> Dict[str , Any] :
    """
    Обрабатывает параметры подбора привода со страницы PaSelectionPage.

    1. Валидирует входные параметры через validate_selection_params().
    2. Определяет рабочее давление (air_pressure_id, по умолчанию 6 бар).
    3. Вызывает BodyThrustTorqueTable.find_suitable_actuators() —
       поиск подходящих корпусов/пружин по моменту с запасом.
    4. Фильтрует серии по взрывозащите (exd_id) — «не хуже чем» по M2M видов
       through-строк PneumaticExdOption.
    5. Логирует все параметры и результаты поиска.

    Returns:
        Dict с ключами success, search_results (список серий с моделями), total_found.
    """
    import json
    from datetime import datetime

    # Нормализация входных параметров (torque_without_safety * safety_factor и т.д.)
    params = _normalize_selection_params(params)

    # Валидация
    is_valid , error_field , error_message , error_fields = validate_selection_params(params)

    if not is_valid :
        print(f"\n❌ ОШИБКА ВАЛИДАЦИИ: {error_message}")
        print(f"Поле с ошибкой: {error_field}")
        return {
            'success' : False ,
            'error' : error_message ,
            'error_field' : error_field ,
            'error_fields' : error_fields
        }

    print("\n" + "=" * 60)
    print("🔍 ПОЛУЧЕН ЗАПРОС НА ПОДБОР ПРИВОДА")
    print("=" * 60)
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📋 ПАРАМЕТРЫ АРМАТУРЫ:")
    print(f"  - Тип арматуры ID: {params.get('valve_type_id')}")
    print(f"  - DN ID: {params.get('dn_id')}")
    print(f"  - PN ID: {params.get('pn_id')}")
    print(f"  - Монтажная площадка ID: {params.get('mounting_plate_id')}")
    print(f"  - Шток ID: {params.get('stem_id')}")

    print("\n⚙️ РАСЧЕТНЫЕ ПАРАМЕТРЫ:")
    print(f"  - Момент без запаса: {params.get('torque_without_safety')} Нм")
    print(f"  - Коэффициент запаса: {params.get('safety_factor')}")
    print(f"  - Момент с запасом: {params.get('torque_with_safety')} Нм")

    print("\n🔧 ТРЕБОВАНИЯ К ПРИВОДУ:")
    print(f"  - Серия моделей ID: {params.get('model_line_id')}")
    print(f"  - Модель в серии ID: {params.get('model_line_item_id')}")
    print(f"  - Вид привода ID: {params.get('actuator_variety_id')}")
    print(f"  - Положение безопасности ID: {params.get('safety_position_id')}")
    print(f"  - Давление в пневмосистеме: {params.get('air_pressure_id')}")
    print(f"  - IP защита ID: {params.get('ip_id')}")
    print(f"  - Exd взрывозащита ID: {params.get('exd_id')}")
    print(f"  - Покрытие корпуса ID: {params.get('coating_id')}")
    print(f"  - Ручной дублер ID: {params.get('manual_override_id')}")

    print("\n🌡️ ТЕМПЕРАТУРНЫЕ ПАРАМЕТРЫ:")
    print(f"  - Мин. температура: {params.get('temp_min')} °C")
    print(f"  - Макс. температура: {params.get('temp_max')} °C")

    print("\n" + "=" * 60)
    print("✅ ПАРАМЕТРЫ УСПЕШНО ПОЛУЧЕНЫ")
    print("=" * 60 + "\n")

    try :
        result = _search_catalog_items(params, locale=locale)
        result['success'] = True
        result['message'] = 'Параметры получены, поиск выполнен'
        result['params_received'] = params
        return result

    except Exception as e :
        print(f"\n❌ Ошибка при поиске: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success' : False ,
            'error' : f'Ошибка при поиске приводов: {str(e)}' ,
            'params_received' : params
        }
    # model_line_for_IP_list=PneumaticIpOption.get_model_line_for_IP(params.get('ip_id'))
    # print(model_line_for_IP_list)
    # # Здесь будет логика поиска подходящего привода
    # return {
    #     'success' : True ,
    #     'message' : 'Параметры получены' ,
    #     'params_received' : params
    # }

def find_compatible_actuators_by_model_line(
        selected_params: Dict[str, Any]
        ) -> List[Dict[str, Any]]:
    ''' Ищет модель по количеству пружин, моментам, модели'''
    return []
