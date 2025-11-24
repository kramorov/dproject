# # serializers.py
#
#
# from rest_framework import serializers
# from .models import ModelLine, ElectricActuatorData, CableGlandHolesSet, WiringDiagram, ActualActuator
# from params.serializers import ActuatorGearboxOutputTypeTypeSerializer, IpOptionSerializer, \
#     BodyCoatingOptionSerializer, ExdOptionSerializer, BlinkerOptionSerializer, SwitchesParametersSerializer, \
#     EnvTempParametersSerializer, DigitalProtocolsSupportOptionSerializer, ControlUnitInstalledOptionSerializer, \
#     HandWheelInstalledOptionSerializer, OperatingModeOptionOptionSerializer, MeasureUnitsSerializer, \
#     MountingPlateTypesSerializer, StemShapesSerializer, StemSizeSerializer, \
#     MechanicalIndicatorInstalledOptionSerializer, PowerSuppliesSerializer
#
# from producers.serializers import BrandsSerializer
# import logging
#
# # Получаем логгер для этого модуля
# logger = logging.getLogger(__name__)
#
#
# class CableGlandHolesSetSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CableGlandHolesSet
#         fields = ['id', 'text_description', 'cg1', 'cg1', 'cg1', 'cg1']
#
#
# # class ActualActuatorSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = ActualActuator
# #         fields = '__all__'
#
#
# class ModelLineSerializer(serializers.ModelSerializer):
#     logging.warning('Вызван метод ModelSerializer')  # Логируем информацию в консоль
#     brand = BrandsSerializer(read_only=True)
#     default_output_type = OperatingModeOptionOptionSerializer(read_only=True)
#     default_ip = IpOptionSerializer(read_only=True)
#     default_body_coating = BodyCoatingOptionSerializer(read_only=True)
#     default_exd = ExdOptionSerializer(read_only=True)
#     default_blinker = BlinkerOptionSerializer(read_only=True)
#     default_end_switches = SwitchesParametersSerializer(read_only=True)
#     default_way_switches = SwitchesParametersSerializer(read_only=True)
#     default_torque_switches = SwitchesParametersSerializer(read_only=True)
#     default_temperature = EnvTempParametersSerializer(read_only=True)
#     default_control_unit_installed = ControlUnitInstalledOptionSerializer(read_only=True)
#     default_hand_wheel = HandWheelInstalledOptionSerializer(read_only=True)
#     default_operating_mode = OperatingModeOptionOptionSerializer(read_only=True)
#
#     class Meta:
#         model = ModelLine
#         fields = '__all__'
#         # fields = ['id', 'name', 'brand', 'default_output_type', 'default_ip', 'default_body_coating', 'default_exd',
#         #           'default_blinker', 'default_end_switches', 'default_way_switches', 'default_torque_switches',
#         #           'default_temperature', 'default_digital_protocol_support', 'default_control_unit_installed',
#         #           'default_hand_wheel', 'default_operating_mode', '']
#
#
# class ElectricActuatorDataSerializer(serializers.ModelSerializer):
#     model_line = ModelLineSerializer(read_only=True)
#     voltage = PowerSuppliesSerializer(read_only=True)
#     rotation_speed_measure_unit = MeasureUnitsSerializer(read_only=True)
#     time_to_open_measure_unit = MeasureUnitsSerializer(read_only=True)
#     mounting_plate = MountingPlateTypesSerializer(many=True, read_only=True)
#     stem_shape = StemShapesSerializer(read_only=True)
#     cable_glands_holes = CableGlandHolesSetSerializer(read_only=True)
#
#     class Meta:
#         model = ElectricActuatorData
#         fields = '__all__'
#         # fields = ['id', 'name', 'model_line', 'voltage', 'weight', 'rotation_speed', 'rotation_speed_measure_unit', \
#         #           'time_to_open', 'time_to_open_measure_unit', 'torque_min', 'torque_max', 'mounting_plate', \
#         #           'stem_shape', 'stem_size', 'max_stem_height', 'max_stem_diameter', 'cable_glands_holes', \
#         #           'motor_power', \
#         #           'motor_power_measure_unit', 'motor_current_rated', 'motor_current_rated_measure_unit', \
#         #           'motor_current_starting', 'motor_current_starting_measure_unit']
#
#
# class WiringDiagramSerializer(serializers.ModelSerializer):
#     applies_to_models = ElectricActuatorDataSerializer(many=True)
#     applies_to_model_lines = ModelLineSerializer(read_only=True)
#
#     class Meta:
#         model = WiringDiagram
#         fields = ['id', 'name', 'applies_to_model_lines', 'applies_to_models']
#         # fields = ['id', 'name', 'applies_to_model_line']
#
#     def validate_applies_to_electric_actuators(self, value):
#         model_line_id = self.initial_data.get('applies_to_model_line')
#         if model_line_id:
#             model_line = ModelLine.objects.get(id=model_line_id)
#             for actuator in value:
#                 if actuator['model_line'] != model_line.id:
#                     raise serializers.ValidationError(f"ElectricActuatorData must belong to the selected ModelLine.")
#         return value
#
#
# class TextInputSerializer(serializers.Serializer):
#     input_text = serializers.CharField()
#
#
# class ActualActuatorSerializer(serializers.ModelSerializer):
#     logging.warning('Вызван метод ActualActuatorSerializer')  # Логируем информацию в консоль
#     actual_model = ElectricActuatorDataSerializer(read_only=True)
#     actual_model_name = serializers.SerializerMethodField()
#     actual_time_to_open_measure_unit = MeasureUnitsSerializer(read_only=True)
#     actual_rotations_to_open_measure_unit = MeasureUnitsSerializer(read_only=True)
#     actual_mounting_plate = MountingPlateTypesSerializer(many=True, read_only=True)
#     actual_stem_shape = StemShapesSerializer(read_only=True)
#     actual_stem_size = StemSizeSerializer(read_only=True)
#     actual_cable_glands_holes = CableGlandHolesSetSerializer(read_only=True)
#     actual_wiring_diagram = WiringDiagramSerializer(read_only=True)
#     actual_ip = IpOptionSerializer(read_only=True)
#     actual_body_coating = BodyCoatingOptionSerializer(read_only=True)
#     actual_exd = ExdOptionSerializer(read_only=True)
#     actual_blinker = BlinkerOptionSerializer(read_only=True)
#     actual_end_switches = SwitchesParametersSerializer(read_only=True)
#     actual_way_switches = SwitchesParametersSerializer(read_only=True)
#     actual_torque_switches = SwitchesParametersSerializer(read_only=True)
#     actual_output_type = ActuatorGearboxOutputTypeTypeSerializer(read_only=True)
#     actual_temperature = EnvTempParametersSerializer(read_only=True)
#     actual_digital_protocol_support = DigitalProtocolsSupportOptionSerializer(read_only=True)
#     actual_control_unit_installed = ControlUnitInstalledOptionSerializer(read_only=True)
#     actual_mechanical_indicator = MechanicalIndicatorInstalledOptionSerializer(read_only=True)
#     actual_hand_wheel = HandWheelInstalledOptionSerializer(read_only=True)
#     actual_operating_mode = OperatingModeOptionOptionSerializer(read_only=True)
#
#     class Meta:
#         model = ActualActuator
#         fields = '__all__'
#
#     def get_actual_model_name(self, obj):
#         # Получаем имя модели привода из вложенного объекта actual_model
#         if obj.actual_model:
#             return_value = '' + obj.actual_model.name + '.' + obj.actual_model.voltage.symbolic_code
#             # return obj.actual_model.name  # Предполагается, что actual_model - это внешний ключ или связь
#             return return_value
#         return ''
