# # electric_actuators/models/ea_actual_actuator.py
# from django.db import models
# from django.utils.timezone import now
#
# class ActualActuator(models.Model) :
#     # Определение полей:
#     PROJECT_STATUS = [
#         ('Draft' , 'Проект') ,  # ('AC', 'Постоянный ток')
#         ('Approved' , 'Утвержден') ,  # ('DC', 'Переменный ток')
#     ]
#     status = models.CharField(max_length=10 , choices=PROJECT_STATUS , default='Draft')
#     date_created = models.DateTimeField(auto_now_add=True , editable=False)
#     date_updated = models.DateTimeField(default=now , editable=False)
#     name = models.CharField(max_length=200 , default='Проект' ,
#                             help_text='Полное название модели привода с опциями и исполнением')
#     actual_model = \
#         models.ForeignKey('ElectricActuatorData' , null=True ,
#                           related_name='actual_model' ,
#                           on_delete=models.SET_NULL , help_text='Базовая модель')
#     actual_time_to_open = models.PositiveIntegerField(blank=True , null=True , help_text='Время поворота')
#     actual_time_to_open_measure_unit = models.ForeignKey('MeasureUnits' ,
#                                                          related_name='actual_actuator_data_time_to_open' ,
#                                                          null=True , blank=True ,
#                                                          on_delete=models.SET_NULL ,
#                                                          help_text='Ед.изм. времени поворота')
#     actual_rotations_to_open = models.PositiveIntegerField(blank=True , null=True ,
#                                                            help_text='Скорость')
#     actual_rotations_to_open_measure_unit = models.ForeignKey('MeasureUnits',
#                                                               related_name='actual_rotations_to_open_measure_unit' ,
#                                                               null=True ,
#                                                               blank=True , on_delete=models.SET_NULL ,
#                                                               help_text='Ед.изм. времени поворота')
#     actual_mounting_plate = models.ManyToManyField('MountingPlateTypes' , blank=True ,
#                                                    related_name='actual_mounting_plate' ,
#                                                    help_text='Монтажная площадка')
#     actual_stem_shape = models.ForeignKey('StemShapes' , on_delete=models.SET_NULL , null=True , blank=True ,
#                                           related_name='actual_stem_shape' ,
#                                           help_text='Тип отверстия под шток арматуры')
#     actual_stem_size = models.ForeignKey('StemSize' , on_delete=models.SET_NULL , null=True , blank=True ,
#                                          related_name='actual_stem_size' ,
#                                          help_text='Размер отверстия под шток арматуры')
#     # actual_cable_glands_holes = models.ForeignKey('CableGlandHolesSet ' , related_name='actual_cable_glands_holes' ,
#     #                                               on_delete=models.SET_NULL , null=True , blank=True ,
#     #                                               help_text='Отверстия под кабельные вводы')
#
#     # actual_wiring_diagram = models.ForeignKey('WiringDiagram' , related_name='actual_wiring_diagram' ,
#     #                                           on_delete=models.SET_NULL , null=True , blank=True ,
#     #                                           help_text='Схема подключения')
#     actual_ip = models.ForeignKey('IpOption' , related_name='actual_ip' , blank=True , null=True ,
#                                   on_delete=models.SET_NULL , help_text='Степень IP')
#     actual_body_coating = models.ForeignKey('BodyCoatingOption' , related_name='actual_body_coating' , blank=True ,
#                                             null=True ,
#                                             on_delete=models.SET_NULL , help_text='Покрытие корпуса')
#     actual_exd = models.ForeignKey('ExdOption' , related_name='actual_exd' , blank=True , null=True ,
#                                    on_delete=models.SET_NULL , help_text='Степень exd')
#     actual_blinker = models.ForeignKey('BlinkerOption' , related_name='actual_blinker' , blank=True , null=True ,
#                                        on_delete=models.SET_NULL , help_text='Блинкер')
#     actual_end_switches = models.ForeignKey('SwitchesParameters' , related_name='actual_end_switches' , blank=True ,
#                                             null=True ,
#                                             on_delete=models.SET_NULL , help_text='Концевые выключатели')
#     actual_way_switches = models.ForeignKey('SwitchesParameters', related_name='actual_way_switches' , blank=True ,
#                                             null=True , on_delete=models.SET_NULL , help_text='Путевые выключатели')
#     actual_torque_switches = models.ForeignKey('SwitchesParameters' , related_name='actual_torque_switches' , blank=True ,
#                                                null=True , on_delete=models.SET_NULL , help_text='Ограничители момента')
#     actual_output_type = models.ForeignKey('ActuatorGearboxOutputType', related_name='actual_output_type' , blank=True ,
#                                            null=True ,
#                                            on_delete=models.SET_NULL , help_text='Вид привода')
#     actual_temperature = models.ForeignKey('EnvTempParameters' , related_name='actual_output_type' , blank=True ,
#                                            null=True , on_delete=models.SET_NULL , help_text='Температурное исполнение')
#
#     actual_digital_protocol_support = models.ForeignKey('DigitalProtocolsSupportOption' ,
#                                                         related_name='actual_digital_protocol_support' , blank=True ,
#                                                         null=True , on_delete=models.SET_NULL ,
#                                                         help_text='Поддержка цифровых протоколов')
#     actual_control_unit_installed = models.ForeignKey('ControlUnitInstalledOption',
#                                                       related_name='actual_control_unit_installed' , blank=True ,
#                                                       null=True , on_delete=models.SET_NULL ,
#                                                       help_text='Блок управления')
#     actual_mechanical_indicator = \
#         models.ForeignKey('MechanicalIndicatorInstalledOption', blank=True , null=True ,
#                           related_name='actual_mechanical_indicator' ,
#                           on_delete=models.SET_NULL ,
#                           help_text='Установленный механический индикатор')
#
#     actual_hand_wheel = models.ForeignKey('HandWheelInstalledOption', related_name='actual_hand_wheel' , blank=True ,
#                                           null=True , on_delete=models.SET_NULL , help_text='Ручной дублер')
#
#     actual_operating_mode = models.ForeignKey('OperatingModeOption' , related_name='actual_operating_mode' , blank=True ,
#                                               null=True , on_delete=models.SET_NULL , help_text='Режим работы')
#     text_description = models.CharField(max_length=1000 ,
#                                         blank=True , null=True ,
#                                         help_text='Полное описание привода с опциями и вариантами исполнения')
#     def get_full_description(self) :
#         data = [
#             {'param_name' : 'name' ,
#              'param_text' : 'Полное название модели привода с опциями и исполнением' , 'param_value' : self.name} ,
#             {'param_name' : 'actual_model' , 'param_text' : 'Базовая модель' ,
#              'param_value' : self.actual_model} ,
#             {'param_name' : 'actual_time_to_open' , 'param_text' : 'Время поворота' ,
#              'param_value' : self.actual_time_to_open} ,
#             {'param_name' : 'actual_time_to_open_measure_unit' ,
#              'param_text' : 'Ед.изм. времени поворота' , 'param_value' : self.actual_time_to_open_measure_unit} ,
#             {'param_name' : 'actual_rotations_to_open' , 'param_text' : 'Скорость' ,
#              'param_value' : self.actual_rotations_to_open} ,
#             {'param_name' : 'actual_rotations_to_open_measure_unit' ,
#              'param_text' : 'Ед.изм. скорости поворота' , 'param_value' : self.actual_rotations_to_open_measure_unit} ,
#             {'param_name' : 'actual_mounting_plate' , 'param_text' : 'Монтажная площадка' ,
#              'param_value' : self.actual_mounting_plate} ,
#             {'param_name' : 'actual_stem_shape' ,
#              'param_text' : 'Тип отверстия под шток арматуры' , 'param_value' : self.actual_stem_shape} ,
#             {'param_name' : 'actual_stem_size' ,
#              'param_text' : 'Размер отверстия под шток арматуры' , 'param_value' : self.actual_stem_size} ,
#             {'param_name' : 'actual_cable_glands_holes' ,
#              'param_text' : 'Отверстия под кабельные вводы' ,
#              'param_value' : self.actual_cable_glands_holes.text_description} ,
#             {'param_name' : 'actual_wiring_diagram' , 'param_text' : 'Схема подключения' ,
#              'param_value' : self.actual_wiring_diagram} ,
#             {'param_name' : 'actual_ip' , 'param_text' : 'IP' , 'param_value' : self.actual_ip} ,
#             {'param_name' : 'actual_body_coating' , 'param_text' : 'Покрытие корпуса' ,
#              'param_value' : self.actual_body_coating} ,
#             {'param_name' : 'actual_exd' , 'param_text' : 'exd' , 'param_value' : self.actual_exd} ,
#             {'param_name' : 'actual_blinker' , 'param_text' : 'Блинкер' ,
#              'param_value' : self.actual_blinker} ,
#             {'param_name' : 'actual_end_switches' , 'param_text' : 'Концевые выключатели' ,
#              'param_value' : self.actual_end_switches} ,
#             {'param_name' : 'actual_way_switches' , 'param_text' : 'Путевые выключатели' ,
#              'param_value' : self.actual_way_switches} ,
#             {'param_name' : 'actual_torque_switches' , 'param_text' : 'Ограничители момента' ,
#              'param_value' : self.actual_torque_switches} ,
#             {'param_name' : 'actual_output_type' , 'param_text' : 'Вид привода' ,
#              'param_value' : self.actual_output_type} ,
#             {'param_name' : 'actual_temperature' , 'param_text' : 'Температурное исполнение' ,
#              'param_value' : self.actual_temperature} ,
#             {'param_name' : 'actual_digital_protocol_support' ,
#              'param_text' : 'Поддержка цифровых протоколов' , 'param_value' : self.actual_digital_protocol_support} ,
#             {'param_name' : 'actual_control_unit_installed' , 'param_text' : 'Блок управления' ,
#              'param_value' : self.actual_control_unit_installed} ,
#             {'param_name' : 'actual_hand_wheel' , 'param_text' : 'Ручной дублер' ,
#              'param_value' : self.actual_hand_wheel} ,
#             {'param_name' : 'actual_operating_mode' , 'param_text' : 'Режим работы' ,
#              'param_value' : self.actual_operating_mode}
#         ]
#         return data
#
#     def make_actual_name(self) :
#         actual_model_var = self.actual_model
#         actual_model_line_var = actual_model_var.model_line
#         actual_model_body_var = actual_model_var.model_body
#         name_str = actual_model_var.name + '.'
#         if self.actual_temperature != actual_model_line_var.default_temperature :
#             name_str = name_str + '.' + self.actual_temperature.symbolic_code
#         if self.actual_ip != actual_model_line_var.default_ip :
#             name_str = name_str + '.' + self.actual_ip.symbolic_code
#         if self.actual_hand_wheel != actual_model_line_var.default_hand_wheel :
#             name_str = name_str + '.' + self.actual_hand_wheel.symbolic_code
#         if self.actual_control_unit_installed != actual_model_line_var.default_control_unit_installed :
#             name_str = name_str + '.' + self.default_control_unit_installed.symbolic_code
#         # if self.actual_digital_protocol_support != self.actual_model.model_line.default_control_unit_installed:
#         #     name_str = name_str + '.' + self.actual_digital_protocol_support.symbolic_code
#         name_str = name_str + '.' + self.actual_model.voltage.symbolic_code
#         if self.actual_exd != actual_model_line_var.default_exd :
#             name_str = name_str + '.' + self.actual_exd.symbolic_code
#
#         make_options_str = ''
#         if self.actual_body_coating != actual_model_line_var.default_body_coating :
#             make_options_str = make_options_str + 'Покрытие корпуса:' + self.actual_body_coating.symbolic_code
#         # if self.actual_mounting_plate != self.actual_model.model_body.mounting_plate:
#         #     make_options_str = make_options_str + '; Монтажная площадка:' + self.actual_mounting_plate.symbolic_code
#         if self.actual_stem_shape != self.actual_model.model_body.stem_shape :
#             make_options_str = make_options_str + '; Тип штока:' + self.actual_stem_shape.symbolic_code
#         if self.actual_stem_size != self.actual_model.model_body.stem_size :
#             make_options_str = make_options_str + '; Размер штока:' + self.actual_stem_size.symbolic_code
#         if self.actual_cable_glands_holes != self.actual_model.model_body.default_cable_glands_holes :
#             make_options_str = make_options_str + '; Размер штока:' + self.actual_cable_glands_holes.name
#
#         if len(make_options_str) > 0 :
#             name_str = name_str + 'Вариант исполнения: ' + make_options_str
#
#         self.name = name_str
#
#
#     def set_actual_time_to_open(self , new_time_to_open) :
#         self.actual_time_to_open = new_time_to_open
#
#     def set_actual_time_to_open_measure_unit(self , new_time_to_open_measure_unit) :
#         self.actual_time_to_open_measure_unit = new_time_to_open_measure_unit
#
#     def set_actual_rotations_to_open(self , new_rotation_speed) :
#         self.actual_rotations_to_open = new_rotation_speed
#
#     def set_actual_rotations_to_open_measure_unit(self , new_rotation_speed_measure_unit) :
#         self.actual_rotations_to_open_measure_unit = new_rotation_speed_measure_unit
#
#     def set_actual_mounting_plate(self , new_mounting_plate) :
#         self.actual_mounting_plate = new_mounting_plate
#         self.make_actual_name()
#
#     def set_actual_stem_shape(self , new_stem_shape) :
#         self.actual_stem_shape = new_stem_shape
#         self.make_actual_name()
#
#     def set_actual_stem_size(self , new_stem_size) :
#         self.actual_stem_size = new_stem_size
#         self.make_actual_name()
#
#     def set_actual_cable_glands_holes(self , new_cable_glands_holes) :
#         self.actual_cable_glands_holes = new_cable_glands_holes
#         self.make_actual_name()
#
#     def set_actual_wiring_diagram(self , new_wiring_diagrams) :
#         self.actual_wiring_diagram = new_wiring_diagrams
#
#     def set_actual_ip(self , new_ip) :
#         self.actual_ip = new_ip
#         self.make_actual_name()
#
#     def set_actual_exd(self , new_exd) :
#         self.actual_exd = new_exd
#         self.make_actual_name()
#
#     def set_actual_blinker(self , new_blinker) :
#         self.actual_blinker = new_blinker
#
#     def set_actual_end_switches(self , new_end_switches) :
#         self.set_actual_end_switches = new_end_switches
#
#     def set_actual_way_switches(self , new_way_switches) :
#         self.actual_way_switches = new_way_switches
#
#     def set_actual_torque_switches(self , new_torque_switches) :
#         self.actual_torque_switches = new_torque_switches
#         self.make_actual_name()
#
#     def set_actual_output_type(self , new_output_type) :
#         self.actual_output_type = new_output_type
#
#     def set_actual_temperature(self , new_temperature) :
#         self.actual_temperature = new_temperature
#         self.make_actual_name()
#
#     def set_actual_digital_protocol_support(self , new_digital_protocol_support) :
#         self.actual_digital_protocol_support = new_digital_protocol_support
#         self.make_actual_name()
#
#     def set_actual_control_unit_installed(self , new_control_unit_installed) :
#         self.actual_control_unit_installed = new_control_unit_installed
#         self.make_actual_name()
#
#     def set_actual_hand_wheel(self , new_hand_wheel) :
#         self.actual_hand_wheel = new_hand_wheel
#         self.make_actual_name()
#
#     def set_actual_body_coating(self , new_body_coating) :
#         self.actual_body_coating = new_body_coating
#         self.make_actual_name()
#
#     def set_actual_operating_mode(self , new_operating_mode) :
#         self.actual_operating_mode = new_operating_mode
#
#     def set_actual_mechanical_indicator(self , new_mechanical_indicator) :
#         self.actual_mechanical_indicator = new_mechanical_indicator
#
#
#
#     def __str__(self) :
#         return self.name
