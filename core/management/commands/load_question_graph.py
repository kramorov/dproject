"""Load QuestionGraph for pneumatic fittings and BKV."""
from django.core.management.base import BaseCommand
from core.models.question_graph import QuestionGraph
from core.models.equipment_type import EquipmentType


class Command(BaseCommand):
    help = 'Load QuestionGraph for pneumatic fittings and BKV'

    def handle(self, *args, **options):
        # ── Pneumatic fittings ──
        et = EquipmentType.objects.filter(code='fittings').first()
        if et:
            pipe_ids = {"1":"pipe_params","2":"pipe_params","5":"pipe_params","6":"pipe_params",
                        "7":"pipe_params","8":"pipe_params","9":"pipe_params","10":"pipe_params"}
            no_pipe_ids = {"3":"thread_params","4":"thread_params"}

            graph_json = {
                "entry_node": "fitting_variety",
                "nodes": {
                    "fitting_variety": {
                        "question": "Тип фитинга",
                        "description": "Выберите тип пневматического фитинга",
                        "param_name": "fitting_variety_id",
                        "branches": {**pipe_ids, **no_pipe_ids, "__default__": "pipe_params"}
                    },
                    "pipe_params": {
                        "question": "Трубка",
                        "description": "Параметры трубки",
                        "param_names": ["pipe_diameter", "pipe_material_id"]
                    },
                    "thread_params": {
                        "question": "Резьба",
                        "description": "Параметры резьбового соединения",
                        "pages": [
                            {"title": "Тип резьбы", "param_names": ["thread_type_id"]},
                            {"title": "Размер резьбы", "param_names": ["thread_id"]},
                            {"title": "Нар/внут", "param_names": ["thread_inner_outer_id"]}
                        ]
                    },
                    "material_params": {
                        "question": "Материал и условия",
                        "description": "Материал корпуса и температурный режим",
                        "param_names": ["body_material_id", "temp_min"]
                    }
                },
                "edges": [
                    {"from": "pipe_params", "to": "thread_params"},
                    {"from": "thread_params", "to": "material_params"}
                ]
            }

            graph, created = QuestionGraph.objects.update_or_create(
                code='pneumatic_fittings',
                defaults={
                    'name': 'Подбор пневмофитингов',
                    'equipment_type': et,
                    'graph_json': graph_json,
                    'is_active': True,
                }
            )
            self.stdout.write(self.style.SUCCESS(
                'Graph fittings: ' + ('Created' if created else 'Updated')
            ))

        # ── BKV (limit switch) ──
        et_lsb = EquipmentType.objects.filter(code='lsb').first()
        if et_lsb:
            graph_lsb = {
                "entry_node": "sensor_variety",
                "nodes": {
                    "sensor_variety": {
                        "question": "Тип датчика",
                        "description": "Выберите тип датчика БКВ",
                        "param_name": "sensor_variety_id",
                        "branches": {"__default__": "common_params"}
                    },
                    "common_params": {
                        "question": "Основные параметры",
                        "description": "Количество точек, корпус, тип сигнала",
                        "pages": [
                            {"title": "Количество точек", "param_names": ["points_id"]},
                            {"title": "Корпус и сигнал", "param_names": ["body_material_id", "signal_type_id"]}
                        ]
                    },
                    "protection_params": {
                        "question": "Защита и условия",
                        "description": "IP, Ex, климат, температура",
                        "pages": [
                            {"title": "IP и Ex", "param_names": ["ip_id", "exd_id"]},
                            {"title": "Температура и климат", "param_names": ["temp_min", "climate_id"]}
                        ]
                    }
                },
                "edges": [
                    {"from": "common_params", "to": "protection_params"}
                ]
            }

            graph, created = QuestionGraph.objects.update_or_create(
                code='lsb',
                defaults={
                    'name': 'Подбор БКВ',
                    'equipment_type': et_lsb,
                    'graph_json': graph_lsb,
                    'is_active': True,
                }
            )
            self.stdout.write(self.style.SUCCESS(
                'Graph BKV: ' + ('Created' if created else 'Updated')
            ))

        # ── Flat graphs for remaining catalogs ──
        flat_graphs = {
            'directional-valve': (
                'Подбор соленоидных клапанов',
                ['model_line_id', 'brand_id', 'function_id', 'actuation_id',
                 'power_supply_id', 'body_material_id', 'solenoid_body_material_id',
                 'pneumatic_connection_id', 'pneumatic_connection_thread_id',
                 'ip_id', 'exd_id', 'climate_id', 'kv_min']
            ),
            'fr': (
                'Подбор фильтр-регуляторов',
                ['model_line_id', 'brand_id', 'filtration_id', 'body_material_id',
                 'flow_rate', 'thread_id', 'thread_type_id', 'temp_min', 'temp_max',
                 'climate_id']
            ),
            'manual-override': (
                'Подбор ручных дублёров',
                ['model_line_id', 'brand_id', 'ip_id', 'body_material_id',
                 'torque', 'mounting_plate_id', 'temp_min', 'temp_max', 'climate_id']
            ),
        }

        for code, (name, params) in flat_graphs.items():
            et = EquipmentType.objects.filter(code=code).first()
            if not et:
                continue
            graph_json = {
                "entry_node": "all_params",
                "nodes": {
                    "all_params": {
                        "question": "Параметры",
                        "param_names": params
                    }
                },
                "edges": []
            }
            graph, created = QuestionGraph.objects.update_or_create(
                code=code,
                defaults={
                    'name': name,
                    'equipment_type': et,
                    'graph_json': graph_json,
                    'is_active': True,
                }
            )
            self.stdout.write(self.style.SUCCESS(
                f'Graph {code}: ' + ('Created' if created else 'Updated')
            ))
