from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def create_predefined_parameters(sender, **kwargs):
    if sender.name == 'your_app_name':
        from .models import WeightDimensionParameterVariety
        WeightDimensionParameterVariety.get_or_create_predefined()