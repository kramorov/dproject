"""Load QuestionGraph for all equipment types."""
from django.core.management.base import BaseCommand
from core.models.question_graph import QuestionGraph
from core.models.equipment_type import EquipmentType


class Command(BaseCommand):
    help = 'Load QuestionGraph for all catalogs'

    def handle(self, *args, **options):
        # ──────────────────────────────────────────
        # Pneumatic fittings
        # ──────────────────────────────────────────
        et = EquipmentType.objects.filter(code='fittings').first()
        if et:
            graph_json = {
                "entry_node": "page_equipment",
                "nodes": {
                    "page_equipment": {
                        "type": "page", "name": "Вид фитинга",
                        "description": "Выберите вид пневматического фитинга",
                        "params": [{"title": "Вид фитинга", "param_name": "equipment_type_id", "order": 1}],
                        "_x": 80, "_y": 60,
                    },
                    "branch_equipment": {
                        "type": "branch", "name": "По виду фитинга", "param_name": "equipment_type_id",
                        "description": "Ветвление по виду фитинга",
                        "match_values": ["17"],
                        "match_target": "page_pipe",
                        "else_target": "page_thread",
                        "_x": 80, "_y": 240,
                    },
                    "page_pipe": {
                        "type": "page", "name": "Параметры трубки",
                        "description": "Параметры трубки",
                        "params": [
                            {"title": "Диаметр трубки", "param_name": "pipe_diameter", "order": 1},
                            {"title": "Материал трубки", "param_name": "pipe_material_id", "order": 2},
                        ],
                        "_x": -100, "_y": 420,
                    },
                    "page_thread": {
                        "type": "page", "name": "Параметры резьбы",
                        "description": "Параметры резьбового соединения",
                        "params": [
                            {"title": "Тип резьбы", "param_name": "thread_type_id", "order": 1},
                            {"title": "Размер резьбы", "param_name": "thread_id", "order": 2},
                            {"title": "Нар/внут", "param_name": "thread_inner_outer_id", "order": 3},
                        ],
                        "_x": 280, "_y": 420,
                    },
                    "page_material": {
                        "type": "page", "name": "Материал и температура",
                        "description": "Материал корпуса и температурный режим",
                        "params": [
                            {"title": "Материал корпуса", "param_name": "body_material_id", "order": 1},
                            {"title": "Температура мин", "param_name": "temp_min", "order": 2},
                        ],
                        "_x": 80, "_y": 600,
                    },
                },
                "edges": [
                    {"from": "page_equipment", "to": "branch_equipment"},
                    {"from": "branch_equipment", "to": "page_pipe", "label": ""},
                    {"from": "branch_equipment", "to": "page_thread", "label": ""},
                    {"from": "page_pipe", "to": "page_thread"},
                    {"from": "page_thread", "to": "page_material"},
                ],
            }
            QuestionGraph.objects.update_or_create(
                code='pneumatic_fittings',
                defaults={'name': 'Подбор пневмофитингов', 'equipment_type': et, 'graph_json': graph_json, 'is_active': True},
            )
            self.stdout.write(self.style.SUCCESS('Graph pneumatic_fittings: Updated'))

        # ──────────────────────────────────────────
        # BKV (limit switch box)
        # ──────────────────────────────────────────
        et_lsb = EquipmentType.objects.filter(code='lsb').first()
        if et_lsb:
            graph_lsb = {
                "entry_node": "page_sensor",
                "nodes": {
                    "page_sensor": {
                        "type": "page", "name": "Тип датчика",
                        "description": "Выберите тип датчика БКВ",
                        "params": [{"title": "Тип датчика", "param_name": "sensor_variety_id", "order": 1}],
                        "_x": 80, "_y": 60,
                    },
                    "branch_sensor": {
                        "type": "branch", "name": "По типу датчика", "param_name": "sensor_variety_id",
                        "description": "Ветвление по типу датчика",
                        "match_values": ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
                        "match_target": "page_common",
                        "else_target": "page_common",
                        "_x": 80, "_y": 240,
                    },
                    "page_common": {
                        "type": "page", "name": "Основные параметры",
                        "description": "Количество точек, тип сигнала, форма контактов, материал корпуса, IP, взрывозащита",
                        "params": [
                            {"title": "Количество точек", "param_name": "points_option_id", "order": 1},
                            {"title": "Тип сигнала", "param_name": "signal_type_id", "order": 2},
                            {"title": "Форма контактов", "param_name": "contact_form_id", "order": 3},
                            {"title": "Материал корпуса", "param_name": "body_material_id", "order": 4},
                            {"title": "IP", "param_name": "ip_id", "order": 5},
                            {"title": "Взрывозащита", "param_name": "exd_id", "order": 6},
                        ],
                        "_x": 80, "_y": 420,
                    },
                    "page_temp": {
                        "type": "page", "name": "Температура",
                        "description": "Температура эксплуатации",
                        "params": [{"title": "Температура мин", "param_name": "work_temp_min", "order": 1}],
                        "_x": 80, "_y": 600,
                    },
                },
                "edges": [
                    {"from": "page_sensor", "to": "branch_sensor"},
                    {"from": "branch_sensor", "to": "page_common"},
                    {"from": "page_common", "to": "page_temp"},
                ],
            }
            QuestionGraph.objects.update_or_create(
                code='lsb',
                defaults={'name': 'Подбор БКВ', 'equipment_type': et_lsb, 'graph_json': graph_lsb, 'is_active': True},
            )
            self.stdout.write(self.style.SUCCESS('Graph lsb: Updated'))

        # ──────────────────────────────────────────
        # Directional valves (solenoid)
        # ──────────────────────────────────────────
        et_dv = EquipmentType.objects.filter(code='directional-valve').first()
        if et_dv:
            graph_dv = {
                "entry_node": "page_params",
                "nodes": {
                    "page_params": {
                        "type": "page", "name": "Параметры",
                        "description": "Основные параметры соленоидного клапана",
                        "params": [
                            {"title": "Серия", "param_name": "model_line_id", "order": 1},
                            {"title": "Бренд", "param_name": "brand_id", "order": 2},
                            {"title": "Схема", "param_name": "function_id", "order": 3},
                            {"title": "Управление", "param_name": "actuation_id", "order": 4},
                            {"title": "Напряжение", "param_name": "power_supply_id", "order": 5},
                            {"title": "Материал корпуса", "param_name": "body_material_id", "order": 6},
                            {"title": "Материал соленоида", "param_name": "solenoid_body_material_id", "order": 7},
                            {"title": "Пневмоподключение", "param_name": "pneumatic_connection_id", "order": 8},
                            {"title": "Резьба подключения", "param_name": "pneumatic_connection_thread_id", "order": 9},
                            {"title": "IP", "param_name": "ip_id", "order": 10},
                            {"title": "Ex", "param_name": "exd_id", "order": 11},
                            {"title": "Kv не менее", "param_name": "kv_min", "order": 12},
                            {"title": "Клим. исполнение", "param_name": "climate", "order": 13},
                        ],
                        "_x": 80, "_y": 60,
                    },
                },
                "edges": [],
            }
            QuestionGraph.objects.update_or_create(
                code='directional-valve',
                defaults={'name': 'Подбор соленоидных клапанов', 'equipment_type': et_dv, 'graph_json': graph_dv, 'is_active': True},
            )
            self.stdout.write(self.style.SUCCESS('Graph directional-valve: Updated'))

        # ──────────────────────────────────────────
        # Filter regulators
        # ──────────────────────────────────────────
        et_fr = EquipmentType.objects.filter(code='fr').first()
        if et_fr:
            graph_fr = {
                "entry_node": "page_params",
                "nodes": {
                    "page_params": {
                        "type": "page", "name": "Параметры",
                        "description": "Основные параметры фильтр-регулятора",
                        "params": [
                            {"title": "Серия", "param_name": "model_line_id", "order": 1},
                            {"title": "Бренд", "param_name": "brand_id", "order": 2},
                            {"title": "Фильтрация мин", "param_name": "filtration_rating_min", "order": 3},
                            {"title": "Материал корпуса", "param_name": "body_material_id", "order": 4},
                            {"title": "Расход мин", "param_name": "flow_rate_min", "order": 5},
                            {"title": "Резьба", "param_name": "thread_id", "order": 6},
                            {"title": "Температура мин", "param_name": "work_temp_min", "order": 7},
                            {"title": "Температура макс", "param_name": "work_temp_max", "order": 8},
                            {"title": "Климат", "param_name": "climate", "order": 9},
                        ],
                        "_x": 80, "_y": 60,
                    },
                },
                "edges": [],
            }
            QuestionGraph.objects.update_or_create(
                code='fr',
                defaults={'name': 'Подбор фильтр-регуляторов', 'equipment_type': et_fr, 'graph_json': graph_fr, 'is_active': True},
            )
            self.stdout.write(self.style.SUCCESS('Graph fr: Updated'))

        # ──────────────────────────────────────────
        # Manual override (gearbox)
        # ──────────────────────────────────────────
        et_mo = EquipmentType.objects.filter(code='manual-override').first()
        if et_mo:
            graph_mo = {
                "entry_node": "page_params",
                "nodes": {
                    "page_params": {
                        "type": "page", "name": "Параметры",
                        "description": "Основные параметры ручного дублёра",
                        "params": [
                            {"title": "Серия", "param_name": "model_line_id", "order": 1},
                            {"title": "Бренд", "param_name": "brand_id", "order": 2},
                            {"title": "IP", "param_name": "ip_id", "order": 3},
                            {"title": "Материал корпуса", "param_name": "body_material_id", "order": 4},
                            {"title": "Рабочий момент", "param_name": "min_work_torque", "order": 5},
                            {"title": "Монтажная площадка", "param_name": "mounting_plate_top_id", "order": 6},
                            {"title": "Температура мин", "param_name": "work_temp_min", "order": 7},
                            {"title": "Температура макс", "param_name": "work_temp_max", "order": 8},
                            {"title": "Клим. исполнение", "param_name": "climate", "order": 9},
                        ],
                        "_x": 80, "_y": 60,
                    },
                },
                "edges": [],
            }
            QuestionGraph.objects.update_or_create(
                code='manual-override',
                defaults={'name': 'Подбор ручных дублёров', 'equipment_type': et_mo, 'graph_json': graph_mo, 'is_active': True},
            )
            self.stdout.write(self.style.SUCCESS('Graph manual-override: Updated'))

        # ──────────────────────────────────────────
        # Cable glands (кабельные вводы)
        # ──────────────────────────────────────────
        et_cg = EquipmentType.objects.filter(code='cable-gland').first()
        if et_cg:
            graph_cg = {
                "entry_node": "page_cable_type",
                "nodes": {
                    "page_cable_type": {
                        "type": "page", "name": "Тип кабеля",
                        "description": "Выберите тип кабеля",
                        "params": [{"title": "Тип кабеля", "param_name": "cable_type_id", "order": 1}],
                        "_x": 80, "_y": 60,
                    },
                    "page_thread": {
                        "type": "page", "name": "Присоединение",
                        "description": "Резьба и материал корпуса",
                        "params": [
                            {"title": "Резьба", "param_name": "thread_id", "order": 1},
                            {"title": "Материал корпуса", "param_name": "body_material_id", "order": 2},
                        ],
                        "_x": 80, "_y": 240,
                    },
                    "page_protection": {
                        "type": "page", "name": "Защита",
                        "description": "IP и взрывозащита",
                        "params": [
                            {"title": "IP", "param_name": "ip_id", "order": 1},
                            {"title": "Взрывозащита", "param_name": "exd_id", "order": 2},
                        ],
                        "_x": 80, "_y": 420,
                    },
                },
                "edges": [
                    {"from": "page_cable_type", "to": "page_thread"},
                    {"from": "page_thread", "to": "page_protection"},
                ],
            }
            QuestionGraph.objects.update_or_create(
                code='cable-gland',
                defaults={'name': 'Подбор кабельных вводов', 'equipment_type': et_cg, 'graph_json': graph_cg, 'is_active': True},
            )
            self.stdout.write(self.style.SUCCESS('Graph cable-gland: Updated'))
