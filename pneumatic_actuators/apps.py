from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class PneumaticActuatorConfig(AppConfig) :
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pneumatic_actuators'
    verbose_name = _('Пневмоприводы')

    def ready(self) :
        # Импортируем сигналы
        import pneumatic_actuators.models.pa_params  # noqa
        import pneumatic_actuators.models.pa_body  # noqa
        import pneumatic_actuators.models.pa_model_line  # noqa
        import pneumatic_actuators.models.pa_techdata  # noqa
        import pneumatic_actuators.models.pa_techdata_drawing_item  # noqa
        import pneumatic_actuators.models.pa_torque  # noqa