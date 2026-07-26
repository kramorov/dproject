"""Seed-команда: заполняет справочники конвейера подбора.

Создаёт:
- EquipmentType: actuator, solenoid, bkv, cable_gland, pneumatic_fitting,
  filter_regulator, manual_override, mounting_kit.
- CascadeRule: правила каскада параметров между типами.
- StepConfig: конфигурации шагов (decompose, extract, filter).
"""

from django.core.management.base import BaseCommand
from ai_assistant.models import (
    EquipmentType, CascadeRule, StepConfig, AIPromptTemplate, JSONSchema,
)


class Command(BaseCommand):
    help = "Заполняет справочники EquipmentType, CascadeRule и StepConfig"

    def handle(self, *args, **options):
        self._seed_equipment_types()
        self._seed_cascade_rules()
        self._seed_step_configs()
        self.stdout.write(self.style.SUCCESS("Pipeline seed done."))

    def _seed_equipment_types(self):
        types = [
            {"code": "actuator", "label": "Пневмопривод", "level": 2,
             "filter_endpoint": "/api/pneumatic_actuators/selector/search/",
             "param_semantics": {
                 "torque_nm": {"direction": "min", "label": "не менее"},
                 "ip": {"direction": "min", "label": "не хуже"},
                 "temperature_min": {"direction": "min", "label": "не выше"},
                 "temperature_max": {"direction": "max", "label": "не ниже"},
                 "exd": {"direction": "exact", "label": ""},
             }},
            {"code": "solenoid", "label": "Соленоидный клапан", "level": 3,
             "filter_endpoint": "/api/solenoid_valves/filter/",
             "param_semantics": {
                 "voltage": {"direction": "exact", "label": ""},
                 "function_type": {"direction": "exact", "label": ""},
                 "ip": {"direction": "min", "label": "не хуже"},
                 "exd": {"direction": "exact", "label": ""},
             }},
            {"code": "bkv", "label": "Блок концевых выключателей", "level": 3,
             "filter_endpoint": "/api/options/bkv/filter/",
             "param_semantics": {
                 "exd": {"direction": "exact", "label": ""},
                 "ip": {"direction": "min", "label": "не хуже"},
             }},
            {"code": "cable_gland", "label": "Кабельный ввод", "level": 4,
             "filter_endpoint": "/api/cable_glands/filter/",
             "param_semantics": {
                 "diameter": {"direction": "exact", "label": ""},
                 "armour": {"direction": "exact", "label": ""},
                 "exd": {"direction": "exact", "label": ""},
             }},
            {"code": "pneumatic_fitting", "label": "Пневматический фитинг", "level": 4,
             "filter_endpoint": "/api/pneumatic_fittings/filter/",
             "param_semantics": {}},
            {"code": "filter_regulator", "label": "Фильтр-регулятор", "level": 3,
             "filter_endpoint": "/api/filter_regulator/filter/",
             "param_semantics": {
                 "pressure": {"direction": "min", "label": "не менее"},
             }},
            {"code": "manual_override", "label": "Ручной дублёр", "level": 3,
             "filter_endpoint": "/api/manual_override/filter/",
             "param_semantics": {}},
            {"code": "mounting_kit", "label": "Монтажный комплект", "level": 4,
             "filter_endpoint": "/api/mounting_kit/filter/",
             "param_semantics": {}},
        ]
        for t in types:
            obj, created = EquipmentType.objects.get_or_create(
                code=t["code"],
                defaults={
                    "label": t["label"], "level": t["level"],
                    "filter_endpoint": t["filter_endpoint"],
                    "param_semantics": t["param_semantics"],
                }
            )
            verb = "Created" if created else "Exists"
            self.stdout.write(f"  {verb} EquipmentType: {obj}")

    def _seed_cascade_rules(self):
        et = {e.code: e for e in EquipmentType.objects.all()}
        rules = [
            # actuator → solenoid: порты, namur, расход
            ("actuator", "solenoid", {
                "port_size_npt": "connection_size",
                "namur_interface": "mounting_type",
                "air_consumption_nl_per_cycle": "flow_rate_min",
            }),
            # actuator → bkv: фланец крепления
            ("actuator", "bkv", {
                "mounting_flange": "flange_size",
            }),
            # actuator → manual_override
            ("actuator", "manual_override", {
                "mounting_flange": "flange_size",
            }),
            # actuator → mounting_kit
            ("actuator", "mounting_kit", {
                "mounting_flange": "flange_size",
            }),
            # solenoid → cable_gland: размер резьбы
            ("solenoid", "cable_gland", {
                "thread_size": "thread_size",
            }),
            # bkv → cable_gland
            ("bkv", "cable_gland", {
                "thread_size": "thread_size",
            }),
            # solenoid → pneumatic_fitting
            ("solenoid", "pneumatic_fitting", {
                "connection_size": "connection_size",
            }),
        ]
        for parent_code, child_code, mapping in rules:
            if parent_code in et and child_code in et:
                obj, created = CascadeRule.objects.get_or_create(
                    parent_type=et[parent_code],
                    child_type=et[child_code],
                    defaults={"mapping": mapping},
                )
                verb = "Created" if created else "Exists"
                self.stdout.write(f"  {verb} CascadeRule: {obj}")
            else:
                self.stdout.write(
                    f"  SKIP CascadeRule {parent_code}→{child_code}: type missing"
                )

    def _seed_step_configs(self):
        decompose_prompt = AIPromptTemplate.objects.filter(
            name="decode", is_active=True
        ).order_by("-version").first()

        if not decompose_prompt:
            self.stdout.write(self.style.WARNING(
                "  No active 'decode' prompt found — skip decompose StepConfig"
            ))
        else:
            sc, created = StepConfig.objects.get_or_create(
                step="decompose", equipment_type=None,
                defaults={
                    "prompt_template": decompose_prompt,
                    "model_role": "debug",
                    "output_schema": None,
                }
            )
            verb = "Created" if created else "Exists"
            self.stdout.write(f"  {verb} StepConfig: {sc}")

        # Extract configs — создаются без промптов (их нужно создать отдельно)
        et_codes = ["actuator", "solenoid", "bkv", "cable_gland",
                     "pneumatic_fitting", "filter_regulator", "manual_override", "mounting_kit"]
        et_map = {e.code: e for e in EquipmentType.objects.all()}
        for code in et_codes:
            if code in et_map:
                sc, created = StepConfig.objects.get_or_create(
                    step="extract", equipment_type=et_map[code],
                    defaults={
                        "model_role": "extraction",
                    }
                )
                verb = "Created" if created else "Exists"
                self.stdout.write(f"  {verb} StepConfig: {sc}")
