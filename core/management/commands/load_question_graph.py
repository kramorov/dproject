"""Load QuestionGraph for pneumatic fittings with proper branching."""
from django.core.management.base import BaseCommand
from core.models.question_graph import QuestionGraph
from core.models.equipment_type import EquipmentType


class Command(BaseCommand):
    help = 'Load QuestionGraph for pneumatic fittings'

    def handle(self, *args, **options):
        et = EquipmentType.objects.filter(code='fittings').first()
        if not et:
            self.stdout.write(self.style.ERROR('EquipmentType "fittings" not found'))
            return

        # IDs: 1,2,5,6,7,8,9,10 = фитинги с трубкой; 3,4 = заглушка/глушитель (без трубки)
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
                        {"title": "Тип резьбы",        "param_names": ["thread_type_id"]},
                        {"title": "Размер резьбы",      "param_names": ["thread_id"]},
                        {"title": "Нар/внут",           "param_names": ["thread_inner_outer_id"]}
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
            f'{"Created" if created else "Updated"} graph: {graph.name}'
        ))
