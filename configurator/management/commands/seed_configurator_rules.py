"""Seed ParameterRule and ParameterBinding for БКВ (lsb) catalog.

Creates reusable parameter rules for temperature, Exd, and creates
bindings to the lsb EquipmentType for use in catalog filtering.

Run: python manage.py seed_configurator_rules
"""
from django.core.management.base import BaseCommand
from configurator.models import ParameterRule, ParameterBinding
from core.models import EquipmentType


class Command(BaseCommand):
    help = "Seed ParameterRule and ParameterBinding for БКВ (lsb) catalog"

    def handle(self, *args, **options):
        try:
            lsb = EquipmentType.objects.get(code="lsb")
        except EquipmentType.DoesNotExist:
            self.stderr.write("EquipmentType 'lsb' not found")
            return

        rules_data = [
            {
                "code": "temperature_min",
                "name": "Температура окр. среды (мин)",
                "match_type": "directional",
                "match_config": {"direction": "min"},
                "hardness": "soft",
                "relaxation_strategy": "step",
                "relaxation_config": {"step": 5, "max_steps": 4},
                "priority": 3,
                "bindings": [{"equipment_type": lsb, "param_name": "work_temp_min"}],
            },
            {
                "code": "temperature_max",
                "name": "Температура окр. среды (макс)",
                "match_type": "directional",
                "match_config": {"direction": "max"},
                "hardness": "soft",
                "relaxation_strategy": "step",
                "relaxation_config": {"step": 5, "max_steps": 4},
                "priority": 3,
                "bindings": [{"equipment_type": lsb, "param_name": "work_temp_max"}],
            },
            {
                "code": "exd",
                "name": "Взрывозащита",
                "match_type": "hierarchy",
                "match_config": {
                    "levels": [
                        "общепром",
                        "Ex ia",
                        "Ex ib",
                        "Ex e",
                        "Ex d",
                        "Ex d IIC",
                    ]
                },
                "hardness": "hard",
                "relaxation_strategy": "none",
                "relaxation_config": None,
                "priority": 8,
                "bindings": [{"equipment_type": lsb, "param_name": "exd"}],
            },
            {
                "code": "ip",
                "name": "Степень защиты IP",
                "match_type": "subset",
                "match_config": {"field": "ip_rank"},
                "hardness": "hard",
                "relaxation_strategy": "none",
                "relaxation_config": None,
                "priority": 5,
                "bindings": [{"equipment_type": lsb, "param_name": "ip"}],
            },
        ]

        for rd in rules_data:
            bindings = rd.pop("bindings")
            rule, created = ParameterRule.objects.update_or_create(
                code=rd["code"],
                defaults=rd,
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(f"  {verb} ParameterRule: {rule}")

            for bd in bindings:
                binding, bcreated = ParameterBinding.objects.update_or_create(
                    equipment_type=bd["equipment_type"],
                    param_name=bd["param_name"],
                    defaults={"rule": rule},
                )
                bverb = "Created" if bcreated else "Exists"
                self.stdout.write(f"    {bverb} ParameterBinding: {binding}")

        self.stdout.write(self.style.SUCCESS("Done"))
