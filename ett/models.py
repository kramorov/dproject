# models.py
from django.db import models
from django.db import models
from params.models import ValveTypes, MeasureUnits, ExdOption, IpOption, PowerSupplies

ETT_ACTUATOR_TYPES = [('Электро', 'Электро'), ('Пневмо', 'Пневмо'), ('Электро-гидро', 'Электро-гидро'),
                      ('Пневмо-гидро', 'Пневмо-гидро'), ('Ручной', 'Ручной')]
ETT_ACTUATOR_SPEED = [('Стандарт', 'Стандарт'), ('Быстродействующий', 'Быстродействующий')]


class EttDocument(models.Model):
    name = models.CharField(max_length=50, blank=True, help_text='Короткое название ЕТТ для отображения на экране')
    full_name = models.CharField(max_length=50, blank=True, help_text='Полное название ЕТТ по документам владельца')
    ett_code = models.CharField(max_length=200, blank=True, help_text='Код ЕТТ по кодировке владельца')
    owner_name = models.CharField(max_length=50, blank=True, help_text='Название компании владельца ЕТТ')
    applies_to = models.ManyToManyField(ValveTypes, blank=True,
                                        related_name='ett_applies_to_valve_type',
                                        help_text='Вид арматуры, к которой применимы ett')

    def __str__(self):
        return self.name


class MtrType(models.Model):
    symbolic_code = models.CharField(max_length=5, help_text='Символьное обозначение типа арматуры')
    text_description = models.CharField(max_length=500, blank=True, help_text='Текстовое описание типа арматуры')
    ett_doc = models.ManyToManyField(EttDocument, blank=True,
                                     related_name='ett_document_mtr_type',
                                     help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True, help_text='Номер таблицы в документе')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code + ' - ' + self.text_description


class PnType(models.Model):
    symbolic_code = models.CharField(max_length=5, help_text='Символьная кодировка Pn')
    valve_pn_value = models.IntegerField(help_text='PN, кгс/см²')
    pn_measure_unit = models.ForeignKey(MeasureUnits, default=11, on_delete=models.SET_NULL, null=True,
                                        help_text='Единица измерения Pn')
    def __str__(self):
        return self.symbolic_code+self.pn_measure_unit.text_description


class DnType(models.Model):
    symbolic_code = models.CharField(max_length=5, help_text='Символьная кодировка Dn')
    valve_dn_value = models.IntegerField(help_text='Dn, мм')
    pipe_dn_value = models.IntegerField(blank=True, help_text='Наружный диаметр присоединяемого трубопровода, мм')
    comment = models.CharField(max_length=200, blank=True, help_text='Комментарий')
    ett_doc = models.ManyToManyField(EttDocument, blank=True,
                                     related_name='ett_document_dn_type',
                                     help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code


class EttActuatorType(models.Model):
    symbolic_code = models.CharField(max_length=5, help_text='Символьная кодировка типа привода')
    actuator_type = models.CharField(max_length=20, choices=ETT_ACTUATOR_TYPES)
    actuator_speed = models.CharField(max_length=20, choices=ETT_ACTUATOR_SPEED)
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание типа привода')
    ett_doc = models.ManyToManyField(EttDocument, blank=True,
                                     related_name='ett_document_actuator_type',
                                     help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code

class EttOpenTime(models.Model):
    symbolic_code = models.CharField(max_length=35 , blank=True, help_text='Символьная кодировка времени открытия/закрытия')
    mtr_type = models.ManyToManyField(MtrType, related_name='ett_open_time_mtr_type',
                                         help_text='Тип арматуры, для которой установлено это время открытия/закрытия')
    dn_from = models.IntegerField(help_text='Dn свыше, мм')
    dn_up_to = models.IntegerField(help_text='DN до, включительно, мм')
    time_to_open_min = models.IntegerField(help_text='Минимальное время открытия, с')
    time_to_open_max = models.IntegerField(help_text='Максимальное время открытия, с')
    actuator_speed = models.CharField(max_length=20, choices=ETT_ACTUATOR_SPEED,
                                         help_text='Тип привода (быстродействующий или стандартный)')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание времени открытия')
    ett_doc = models.ManyToManyField(EttDocument, blank=True,
                                     related_name='ett_document_open_time',
                                     help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return f'{self.mtr_type} Dn от {self.dn_from} до (включительно) {self.dn_up_to}'


class EttClimaticOption(models.Model):
    symbolic_code = models.CharField(max_length=5, help_text='Символьная кодировка климатического исполнения')
    work_temp_min = models.IntegerField(help_text='НИЖНЕЕ РАБОЧЕЕ ЗНАЧЕНИЕ ТЕМПЕРАТУРЫ ОКРУЖАЮЩЕГО ВОЗДУХА, ºС')
    work_temp_max = models.IntegerField(help_text='ВЕРХНЕЕ РАБОЧЕЕ ЗНАЧЕНИЕ ТЕМПЕРАТУРЫ ОКРУЖАЮЩЕГО ВОЗДУХА, ºС')
    extremal_temp_min = models.IntegerField(help_text='НИЖНЕЕ ПРЕДЕЛЬНОЕ ЗНАЧЕНИЕ ТЕМПЕРАТУРЫ ОКРУЖАЮЩЕГО ВОЗДУХА, ºС')
    extremal_temp_max = models.IntegerField(help_text='ВЕРХНЕЕ ПРЕДЕЛЬНОЕ ЗНАЧЕНИЕ ТЕМПЕРАТУРЫ ОКРУЖАЮЩЕГО ВОЗДУХА, ºС')
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Текстовое описание климатического исполнения')
    ett_doc = models.ManyToManyField(EttDocument, blank=True,
                                     related_name='ett_document_climatic_option',
                                     help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code


class EttMediumMaxTempOption(models.Model):
    symbolic_code = models.CharField(max_length=5,
                                     help_text='Символьная кодировка Температура рабочей среды (стенки) максимальная расчетная, ºС')
    work_temp_max = models.IntegerField(blank=True,
                                        help_text='Температура рабочей среды (стенки) максимальная расчетная, ºС')
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Текстовое описание Температура рабочей среды (стенки) максимальная расчетная, ºС')
    ett_doc = models.ManyToManyField(EttDocument, blank=True,
                                     related_name='ett_document_medium_max_temp',
                                     help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code


class EttSeismicOption(models.Model):
    symbolic_code = models.CharField(max_length=5, help_text='Символьная кодировка Исполнения по сейсмостойкости')
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Текстовое описание Исполнения по сейсмостойкости')
    ett_doc = models.ManyToManyField(EttDocument, blank=True,
                                     related_name='ett_document_seismic_option',
                                     help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code


class EttStatusSignal(models.Model):
    symbolic_code = models.CharField(max_length=50, help_text='Краткое описание сигнала состояния '
                                                              'Открыто/Закрыто/Стоп/Авария/Дистанционный '
                                                              'режим/Готовность')
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Полное описание описание сигнала состояния '
                                                  'Открыто/Закрыто/Стоп/Авария/Дистанционный режим/Готовность, '
                                                  'тип сигнала и напряжение/протокол передачи ')
    ett_doc = models.ManyToManyField(EttDocument, blank=True,
                                     related_name='ett_document_status_signal',
                                     help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code


class EttControlSignal(models.Model):
    symbolic_code = models.CharField(max_length=50,
                                     help_text='Краткое описание сигнала управления Открыть/Закрыть/Стоп')
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Полное описание описание сигнала управления Открыть/Закрыть/Стоп '
                                                  'тип управляющего сигнала/протокол передачи ')
    ett_doc = models.ManyToManyField(EttDocument, blank=True,
                                     related_name='ett_document_control_signal',
                                     help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code


class EttFeedbackSignal(models.Model):
    symbolic_code = models.CharField(max_length=50, help_text='Символьная кодировка сигнала обратной связи')
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Полное описание описание сигнала сигнала обратной связи')
    ett_doc = models.ManyToManyField(EttDocument, blank=True,
                                     related_name='ett_document_feedback_signal',
                                     help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code


class EttControlUnitHeater(models.Model):
    symbolic_code = models.CharField(max_length=20,
                                     help_text='Символьная кодировка Наличие встроенного электрообогрева блока управления')
    param_name = models.CharField(max_length=100, default='Наличие встроенного электрообогрева блока управления',
                                  help_text='Название параметра Наличие встроенного электрообогрева блока управления')
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Полное описание описание встроенного электрообогрева блока управления')
    ett_doc = models.ManyToManyField(EttDocument, blank=True,
                                     related_name='ett_document_control_unit_heater',
                                     help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code


class EttControlUnitType(models.Model):
    symbolic_code = models.CharField(max_length=20,
                                     help_text='Символьная кодировка Наличие блока управления и его расположение')
    param_name = models.CharField(max_length=100, default='Наличие блока управления и его расположение',
                                  help_text='Название параметра Наличие блока управления и его расположение')
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Наличие блока управления и его расположение ')
    ett_doc = models.ManyToManyField(EttDocument, blank=True,
                                     related_name='ett_document_control_unit_type',
                                     help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code


class EttControlUnitDisplayType(models.Model):
    symbolic_code = models.CharField(max_length=20, help_text='Символьная кодировка Наличие графического дисплея')
    param_name = models.CharField(max_length=100, default='Наличие графического дисплея',
                                  help_text='Название параметра Наличие графического дисплея')
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Наличие графического дисплея')
    ett_doc = models.ManyToManyField(EttDocument, blank=True,
                                     related_name='ett_document_control_unit_display_type',
                                     help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code


class EttCableGlandType(models.Model):
    symbolic_code = models.CharField(max_length=20, help_text='Символьная кодировка типа кабельного ввода')
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Наличие графического дисплея')
    ett_doc = models.ManyToManyField(EttDocument, blank=True,
                                     related_name='ett_document_cable_gland_type',
                                     help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code


class EttElectricOptionsCombination(models.Model):
    symbolic_code = models.CharField(max_length=20, help_text='Символьная кодировка ЭЛЕКТРОТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ')
    exd_choice = models.ForeignKey(ExdOption, on_delete=models.SET_NULL,
                                   related_name='ett_electric_combination_exd_choice', null=True)
    ip_choice = models.ForeignKey(IpOption, on_delete=models.SET_NULL,
                                  related_name='ett_electric_combination_exd_choice', null=True)
    power_choice = models.ForeignKey(PowerSupplies, on_delete=models.SET_NULL,
                                     related_name='ett_electric_combination_power_choice', null=True)
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Текстовое описание кодировки ЭЛЕКТРОТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ')
    ett_doc = models.ForeignKey(EttDocument, blank=True, on_delete=models.SET_NULL, null=True,
                                related_name='ett_document_electric_combination',
                                help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code


class EttControlOptionsCombination(models.Model):
    symbolic_code = models.CharField(max_length=20, help_text='Символьная кодировка Контроль и Управление')
    status_signal_choice = models.ForeignKey(EttStatusSignal, on_delete=models.SET_NULL,
                                             related_name='ett_control_combination_status_signal_choice', null=True, blank=True,
                                        help_text='Сигналы состояния Открыто/Закрыто/Стоп/Авария/Дистанционный режим/Готовность')
    control_signal_choice = models.ForeignKey(EttControlSignal, on_delete=models.SET_NULL,
                                              related_name='ett_control_combination_control_signal_choice', null=True, blank=True,
                                        help_text='Сигналы управления Открыть/Закрыть/Стоп')
    feedback_signal_choice = models.ForeignKey(EttFeedbackSignal, on_delete=models.SET_NULL,
                                               related_name='ett_control_combination_feedback_signal_choice', null=True, blank=True,
                                        help_text='Сигнал обратной связи ')
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Текстовое описание кодировки Контроль и управление')
    ett_doc = models.ForeignKey(EttDocument, blank=True, on_delete=models.SET_NULL, null=True,
                                related_name='ett_document_control_combination',
                                help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code


class EttOtherOptionsCombination(models.Model):
    symbolic_code = models.CharField(max_length=20, help_text='Символьная кодировка ОПЦИИ/КОМПЛЕКТУЮЩИЕ')
    cu_heater_choice = models.ForeignKey(EttControlUnitHeater, on_delete=models.SET_NULL,
                                         related_name='ett_other_options_combination_cu_heater_choice',
                                         help_text='НАЛИЧИЕ ВСТРОЕННОГО ЭЛЕКТРООБОГРЕВА БЛОКА УПРАВЛЕНИЯ', null=True)
    cu_location_choice = models.ForeignKey(EttControlUnitType , on_delete=models.SET_NULL ,
                                           related_name='ett_other_options_combination_cu_location_type_choice' ,
                                           help_text='НАЛИЧИЕ БЛОКА УПРАВЛЕНИЯ И ЕГО РАСПОЛОЖЕНИЕ' , null=True)
    display_choice = models.ForeignKey(EttControlUnitDisplayType, on_delete=models.SET_NULL,
                                       related_name='ett_other_options_combination_display_choice',
                                       help_text='ГРАФИЧЕСКИЙ ДИСПЛЕЙ', null=True)
    cg1_choice = models.ForeignKey(EttCableGlandType, on_delete=models.SET_NULL,
                                   related_name='ett_other_options_combination_cg1_choice',
                                   help_text='КВ1, КАБЕЛЬНЫЙ ВВОД ДЛЯ СИЛОВОГО КАБЕЛЯ', null=True)
    cg23_choice = models.ForeignKey(EttCableGlandType, on_delete=models.SET_NULL,
                                    related_name='ett_other_options_combination_cg23_choice',
                                    help_text='КАБЕЛЬНЫЙ ВВОД КВ2/КВ3 ДЛЯ КОНТРОЛЬНОГО И ИНТЕРФЕЙСНОГО КАБЕЛЕЙ',
                                    null=True)
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Текстовое описание кодировки ОПЦИИ/КОМПЛЕКТУЮЩИЕ')
    ett_doc = models.ForeignKey(EttDocument, blank=True, on_delete=models.SET_NULL, null=True,
                                related_name='ett_document_other_option_combination',
                                help_text='Документ технических требований, где описаны эти требования')
    source_table_number = models.CharField(max_length=50, blank=True,
                                           help_text='Номер таблицы в документе, где описан этот параметр')
    source_table_name = models.CharField(max_length=300, blank=True,
                                         help_text='Название таблицы в документе, где описан этот параметр')

    def __str__(self):
        return self.symbolic_code
