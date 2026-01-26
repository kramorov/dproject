#electric_actuators/admin/ea_wiring_diagram_admin.py
from django.contrib import admin

from django import forms

from electric_actuators.models import WiringDiagram , ElectricActuatorData


class WiringDiagramAdminForm(forms.ModelForm):
    class Meta:
        model = WiringDiagram
        fields = '__all__'

    applies_to_electric_actuators = forms.ModelMultipleChoiceField(
        queryset=ElectricActuatorData.objects.none(),  # initially empty queryset
        widget=forms.CheckboxSelectMultiple,
        required=False  # поле теперь необязательное
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'applies_to_model_line' in self.data:
            try:
                model_line_id = int(self.data.get('applies_to_model_line'))
                self.fields['applies_to_models'].queryset = ElectricActuatorData.objects.filter(
                    model_line_id=model_line_id)
            except (ValueError, TypeError):
                pass

@admin.register(WiringDiagram)
class WiringDiagramAdmin(admin.ModelAdmin):
    form = WiringDiagramAdminForm

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # if obj:  # for editing
        #     form.base_fields[
        #         'applies_to_electric_actuators'].queryset = obj.applies_to_model_line.electric_actuators.all()
        return form