# # valves/forms.py (создайте если нужно)
# from django import forms
#
# from materials.models import MaterialSpecified
# from .models import ValveComponent, ComponentAllowedMaterial, ValveVariety
#
#
# class ValveComponentForm(forms.ModelForm):
#     class Meta:
#         model = ValveComponent
#         fields = '__all__'
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Упрощенные queryset для избежания проблем с фильтрацией
#         self.fields['valve_variety'].queryset = ValveVariety.objects.all()
#
#
# class ComponentAllowedMaterialForm(forms.ModelForm):
#     class Meta:
#         model = ComponentAllowedMaterial
#         fields = '__all__'
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Упрощенные queryset
#         self.fields['valve_component'].queryset = ValveComponent.objects.all()
#         self.fields['material'].queryset = MaterialSpecified.objects.all()
#
#
# # valves/admin.py (дополнение)
# # from .forms import ValveComponentForm, ComponentAllowedMaterialForm
# #
# #
# # @admin.register(ValveComponent)
# # class ValveComponentAdmin(admin.ModelAdmin):
# #     form = ValveComponentForm
# #     # ... остальные настройки ...
# #
# #
# # @admin.register(ComponentAllowedMaterial)
# # class ComponentAllowedMaterialAdmin(admin.ModelAdmin):
# #     form = ComponentAllowedMaterialForm
# #     # ... остальные настройки ...