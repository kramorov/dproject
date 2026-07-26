"""Seed-команда: создаёт JSONSchema, extract-промпты и привязывает StepConfig.

Создаёт:
- JSONSchema (6 шт) — схемы выхода extract-шага для каждого типа оборудования.
- AIPromptTemplate (6 шт) — extract-промпты для каждого типа.
- Обновляет существующие StepConfig (extract/...) — привязывает prompt + schema.
"""

from django.core.management.base import BaseCommand
from ai_assistant.models import JSONSchema, AIPromptTemplate, StepConfig, EquipmentType


# ── JSON-схемы для Фазы 2 (extract) ──────────────────────────────

EXTRACT_SCHEMAS = {
    "actuator": {
        "name": "actuator_filters",
        "description": "Схема фильтров для подбора пневмопривода",
        "schema": {
            "type": "object",
            "properties": {
                "valve_type": {"type": "string", "description": "Тип арматуры: затвор, кран, задвижка"},
                "dn": {"type": "integer", "description": "ДУ (диаметр условный), мм"},
                "pn": {"type": "string", "description": "PN (давление номинальное)"},
                "torque_nm": {"type": "number", "description": "Крутящий момент, Нм"},
                "safety_factor": {"type": "number", "description": "Коэффициент запаса (по умолчанию 1.3)"},
                "actuator_variety": {"type": "string", "description": "Вид привода: DA (двойного действия), SR (пружинный возврат)"},
                "safety_position": {"type": "string", "description": "Положение безопасности: NO (нормально открыт), NC (нормально закрыт) — для SR"},
                "air_pressure_bar": {"type": "number", "description": "Давление в пневмосистеме, бар (по умолчанию 6)"},
                "ip": {"type": "string", "description": "Степень защиты IP: IP65, IP67, IP68"},
                "exd": {"type": "string", "description": "Взрывозащита: общепромышленное, Exd IIC T6, ..."},
                "temperature_min": {"type": "number", "description": "Минимальная температура, °C"},
                "temperature_max": {"type": "number", "description": "Максимальная температура, °C"},
                "hand_wheel": {"type": "boolean", "description": "Требуется ли ручной дублёр"},
                "coating": {"type": "string", "description": "Покрытие корпуса"},
                "stem_shape": {"type": "string", "description": "Форма штока арматуры"},
                "stem_size": {"type": "string", "description": "Размер штока арматуры"},
                "mounting_plate": {"type": "string", "description": "Монтажная площадка (ISO 5211)"},
            },
            "required": ["torque_nm"],
        },
    },
    "solenoid": {
        "name": "solenoid_filters",
        "description": "Схема фильтров для подбора соленоидного клапана",
        "schema": {
            "type": "object",
            "properties": {
                "voltage": {"type": "string", "description": "Напряжение питания: 24V DC, 220V AC, ..."},
                "function_type": {"type": "string", "description": "Схема/функция: 3/2, 5/2, 5/3"},
                "actuation": {"type": "string", "description": "Управление: моностабильный, бистабильный"},
                "connection_size": {"type": "string", "description": "Размер пневматического присоединения: G1/8, G1/4, ..."},
                "kv_min": {"type": "number", "description": "Минимальный Kv (пропускная способность), м³/ч"},
                "body_material": {"type": "string", "description": "Материал корпуса: алюминий, нержавеющая сталь, ..."},
                "solenoid_body_material": {"type": "string", "description": "Материал корпуса соленоида"},
                "ip": {"type": "string", "description": "Степень защиты IP"},
                "exd": {"type": "string", "description": "Взрывозащита"},
                "temperature_min": {"type": "number", "description": "Минимальная рабочая температура, °C"},
                "temperature_max": {"type": "number", "description": "Максимальная рабочая температура, °C"},
                "manual_override": {"type": "boolean", "description": "Наличие ручного дублёра"},
                "mounting_type": {"type": "string", "description": "Тип крепления: namur (на привод), bracket (на скобу), pipe (на трубу)"},
                "flow_rate_min": {"type": "number", "description": "Минимальный расход воздуха (от привода), л/цикл"},
            },
            "required": ["voltage", "function_type"],
        },
    },
    "bkv": {
        "name": "bkv_filters",
        "description": "Схема фильтров для подбора БКВ (блока концевых выключателей)",
        "schema": {
            "type": "object",
            "properties": {
                "exd": {"type": "string", "description": "Взрывозащита: общепромышленное, Exd IIC T6, ..."},
                "ip": {"type": "string", "description": "Степень защиты IP"},
                "sensor_type": {"type": "string", "description": "Тип датчиков: механические, индуктивные, герконовые"},
                "sensor_quantity": {"type": "integer", "description": "Количество датчиков (2-4)"},
                "visual_indicator": {"type": "boolean", "description": "Наличие визуального индикатора"},
                "flange_size": {"type": "string", "description": "Размер фланца крепления (от привода): F05, F07, F10, ..."},
                "temperature_min": {"type": "number", "description": "Минимальная температура, °C"},
                "temperature_max": {"type": "number", "description": "Максимальная температура, °C"},
                "housing_material": {"type": "string", "description": "Материал корпуса"},
            },
            "required": [],
        },
    },
    "cable_gland": {
        "name": "cable_gland_filters",
        "description": "Схема фильтров для подбора кабельного ввода",
        "schema": {
            "type": "object",
            "properties": {
                "exd": {"type": "string", "description": "Взрывозащита: общепромышленное, Exd IIC T6, ..."},
                "armour_type": {"type": "string", "description": "Тип брони: небронированный, бронированный, оплётка"},
                "cable_diameter_min": {"type": "number", "description": "Минимальный диаметр кабеля, мм"},
                "cable_diameter_max": {"type": "number", "description": "Максимальный диаметр кабеля, мм"},
                "thread_size": {"type": "string", "description": "Размер резьбы: M20, M25, G1/2, ..."},
                "material": {"type": "string", "description": "Материал: латунь, нержавеющая сталь, пластик"},
                "ip": {"type": "string", "description": "Степень защиты IP"},
                "temperature_min": {"type": "number", "description": "Минимальная температура, °C"},
                "temperature_max": {"type": "number", "description": "Максимальная температура, °C"},
            },
            "required": [],
        },
    },
    "pneumatic_fitting": {
        "name": "pneumatic_fitting_filters",
        "description": "Схема фильтров для подбора пневматического фитинга",
        "schema": {
            "type": "object",
            "properties": {
                "connection_size": {"type": "string", "description": "Размер присоединения: G1/8, G1/4, 6мм, 8мм, ..."},
                "fitting_type": {"type": "string", "description": "Тип фитинга: прямой, угловой, тройник, переходник"},
                "material": {"type": "string", "description": "Материал: латунь, нерж., пластик"},
                "tube_od": {"type": "number", "description": "Внешний диаметр трубки, мм"},
                "quantity": {"type": "integer", "description": "Количество, шт"},
            },
            "required": [],
        },
    },
    "filter_regulator": {
        "name": "filter_regulator_filters",
        "description": "Схема фильтров для подбора фильтра-регулятора",
        "schema": {
            "type": "object",
            "properties": {
                "connection_size": {"type": "string", "description": "Размер присоединения: G1/4, G3/8, G1/2, ..."},
                "pressure_range": {"type": "string", "description": "Диапазон регулировки давления: 0.5-8 бар, 0.5-10 бар"},
                "filter_rating": {"type": "number", "description": "Тонкость фильтрации, мкм (5, 20, 40)"},
                "flow_rate": {"type": "number", "description": "Расход воздуха, л/мин"},
                "drain_type": {"type": "string", "description": "Тип слива: ручной, автоматический"},
                "with_pressure_gauge": {"type": "boolean", "description": "Наличие манометра"},
            },
            "required": [],
        },
    },
}

# ── Extract-промпты для Фазы 2 ───────────────────────────────────

EXTRACT_PROMPTS = {
    "actuator": {
        "name": "extract_actuator",
        "text": """{system_prompt}

Ты — инженер по подбору пневмоприводов. Извлеки из требований пользователя структурированные параметры для подбора пневмопривода.

ТРЕБОВАНИЯ ПОЛЬЗОВАТЕЛЯ:
{requirements}

ГЛОБАЛЬНЫЕ ТРЕБОВАНИЯ (применяются ко всем компонентам):
{global_requirements}

Верни СТРОГО JSON с полями:
- valve_type: тип арматуры (затвор/кран/задвижка) или null
- dn: ДУ в мм (число) или null
- pn: PN (строка) или null
- torque_nm: крутящий момент в Нм (число) — ОБЯЗАТЕЛЬНО
- safety_factor: коэффициент запаса (по умолчанию 1.3 если не указан)
- actuator_variety: DA или SR
- safety_position: NO или NC (только для SR)
- air_pressure_bar: давление в пневмосистеме, бар (по умолчанию 6)
- ip: степень защиты IP (строка) или null
- exd: взрывозащита (строка) или null
- temperature_min: минимальная температура, °C (число) или null
- temperature_max: максимальная температура, °C (число) или null
- hand_wheel: требуется ли ручной дублёр (true/false)
- coating: покрытие корпуса (строка) или null
- stem_shape: форма штока (строка) или null
- stem_size: размер штока (строка) или null
- mounting_plate: монтажная площадка ISO 5211 (строка) или null

ПРАВИЛА:
1. Бери значения ИЗ ТРЕБОВАНИЙ. Если параметра нет — ставь null.
2. Глобальные требования применяй, если для параметра нет конкретного значения.
3. Для температуры: если указан диапазон "-40…+60", то temperature_min=-40, temperature_max=60.
4. Не додумывай значения, которых нет в тексте.

ФОРМАТ: только JSON, без markdown-обёрток.""",
    },
    "solenoid": {
        "name": "extract_solenoid",
        "text": """{system_prompt}

Ты — инженер по подбору соленоидных клапанов. Извлеки из требований пользователя структурированные параметры.

ТРЕБОВАНИЯ ПОЛЬЗОВАТЕЛЯ:
{requirements}

ГЛОБАЛЬНЫЕ ТРЕБОВАНИЯ:
{global_requirements}

Верни СТРОГО JSON с полями:
- voltage: напряжение питания (24V DC, 220V AC, ...) — ОБЯЗАТЕЛЬНО
- function_type: схема (3/2, 5/2, 5/3) — ОБЯЗАТЕЛЬНО. Если привод DA → 5/2, если SR → 3/2
- actuation: управление (моностабильный/бистабильный) или null
- connection_size: размер пневмоприсоединения (G1/8, G1/4, ...) или null
- kv_min: минимальный Kv (число) или null
- body_material: материал корпуса или null
- solenoid_body_material: материал соленоида или null
- ip: степень защиты IP или null
- exd: взрывозащита или null
- temperature_min: мин. температура, °C или null
- temperature_max: макс. температура, °C или null
- manual_override: наличие ручного дублёра (true/false/null)
- mounting_type: namur/bracket/pipe или null
- flow_rate_min: мин. расход воздуха (л/цикл) или null

ПРАВИЛА:
1. Если явно не указан function_type, но указан тип привода: DA → 5/2, SR → 3/2.
2. Если указан Namur — mounting_type = "namur".
3. Глобальные требования применяй как fallback.

ФОРМАТ: только JSON, без markdown-обёрток.""",
    },
    "bkv": {
        "name": "extract_bkv",
        "text": """{system_prompt}

Ты — инженер по подбору блоков концевых выключателей (БКВ). Извлеки параметры.

ТРЕБОВАНИЯ:
{requirements}

ГЛОБАЛЬНЫЕ ТРЕБОВАНИЯ:
{global_requirements}

Верни СТРОГО JSON:
- exd: взрывозащита или null
- ip: степень защиты IP или null
- sensor_type: механические/индуктивные/герконовые или null
- sensor_quantity: количество датчиков (2-4) или null
- visual_indicator: true/false/null
- flange_size: размер фланца (F05, F07, F10, ...) или null
- temperature_min: мин. температура, °C или null
- temperature_max: макс. температура, °C или null
- housing_material: материал корпуса или null

ФОРМАТ: только JSON, без markdown-обёрток.""",
    },
    "cable_gland": {
        "name": "extract_cable_gland",
        "text": """{system_prompt}

Ты — инженер по подбору кабельных вводов. Извлеки параметры.

ТРЕБОВАНИЯ:
{requirements}

ГЛОБАЛЬНЫЕ ТРЕБОВАНИЯ:
{global_requirements}

Верни СТРОГО JSON:
- exd: взрывозащита или null
- armour_type: небронированный/бронированный/оплётка или null
- cable_diameter_min: мин. диаметр кабеля, мм (число) или null
- cable_diameter_max: макс. диаметр кабеля, мм (число) или null
- thread_size: резьба (M20, M25, G1/2, ...) или null
- material: латунь/нерж./пластик или null
- ip: IP или null
- temperature_min: мин. температура, °C или null
- temperature_max: макс. температура, °C или null

ФОРМАТ: только JSON, без markdown-обёрток.""",
    },
    "pneumatic_fitting": {
        "name": "extract_pneumatic_fitting",
        "text": """{system_prompt}

Ты — инженер по подбору пневматических фитингов. Извлеки параметры.

ТРЕБОВАНИЯ:
{requirements}

ГЛОБАЛЬНЫЕ ТРЕБОВАНИЯ:
{global_requirements}

Верни СТРОГО JSON:
- connection_size: размер присоединения (G1/8, G1/4, 6мм, 8мм, ...) или null
- fitting_type: тип (прямой/угловой/тройник/переходник) или null
- material: материал (латунь/нерж./пластик) или null
- tube_od: внешний диаметр трубки, мм или null
- quantity: количество, шт (число) или null

ФОРМАТ: только JSON, без markdown-обёрток.""",
    },
    "filter_regulator": {
        "name": "extract_filter_regulator",
        "text": """{system_prompt}

Ты — инженер по подбору фильтров-регуляторов. Извлеки параметры.

ТРЕБОВАНИЯ:
{requirements}

ГЛОБАЛЬНЫЕ ТРЕБОВАНИЯ:
{global_requirements}

Верни СТРОГО JSON:
- connection_size: размер присоединения (G1/4, G3/8, ...) или null
- pressure_range: диапазон регулировки или null
- filter_rating: тонкость фильтрации, мкм (5/20/40) или null
- flow_rate: расход, л/мин (число) или null
- drain_type: ручной/автоматический или null
- with_pressure_gauge: наличие манометра (true/false/null)

ФОРМАТ: только JSON, без markdown-обёрток.""",
    },
}


class Command(BaseCommand):
    help = "Создаёт JSONSchema, extract-промпты и привязывает StepConfig"

    def handle(self, *args, **options):
        self._seed_schemas()
        self._seed_prompts()
        self._link_step_configs()
        self.stdout.write(self.style.SUCCESS("Extract phase 2 seed done."))

    def _seed_schemas(self):
        for code, spec in EXTRACT_SCHEMAS.items():
            obj, created = JSONSchema.objects.update_or_create(
                name=spec["name"], version="1",
                defaults={
                    "description": spec["description"],
                    "schema_json": spec["schema"],
                    "is_active": True,
                },
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(f"  {verb} JSONSchema: {obj}")

    def _seed_prompts(self):
        system = AIPromptTemplate.objects.filter(name="system_prompt", is_active=True).first()
        sp = system.template_text if system else "Ты — AI-ассистент компании АБРА."

        for code, spec in EXTRACT_PROMPTS.items():
            text = spec["text"].format(system_prompt=sp, requirements="{requirements}", global_requirements="{global_requirements}")
            obj, created = AIPromptTemplate.objects.update_or_create(
                name=spec["name"], version="1",
                defaults={
                    "description": f"Extract prompt for {code} — Phase 2",
                    "template_text": text,
                    "intent": "extract",
                    "is_active": True,
                },
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(f"  {verb} Prompt: {obj}")

    def _link_step_configs(self):
        et_map = {e.code: e for e in EquipmentType.objects.all()}
        for code in EXTRACT_SCHEMAS:
            if code not in et_map:
                continue
            prompt = AIPromptTemplate.objects.filter(
                name=EXTRACT_PROMPTS[code]["name"], version="1"
            ).first()
            schema = JSONSchema.objects.filter(
                name=EXTRACT_SCHEMAS[code]["name"], version="1"
            ).first()

            sc = StepConfig.objects.filter(
                step="extract", equipment_type=et_map[code]
            ).first()
            if sc:
                sc.prompt_template = prompt
                sc.output_schema = schema
                sc.model_role = "extraction"
                sc.save(update_fields=["prompt_template", "output_schema", "model_role"])
                self.stdout.write(f"  Linked StepConfig: {sc}")
