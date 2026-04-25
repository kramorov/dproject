# pneumatic_actuators/models/pa_body.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union
from django.db.models.signals import pre_save , post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from params.models import MountingPlateTypes , StemShapes , StemSize , ThreadTypes , PneumaticConnection , ThreadSize


# from pneumatic_actuators.models import PneumaticActuatorTechDataTable

class PneumaticActuatorBodyTable(models.Model) :
    """
    Таблица для групповой обработки значений - импорта и экспорта
    """
    name = models.CharField(max_length=100 , blank=True , null=True ,
                            verbose_name=_("Название") ,
                            help_text=_("Название таблицы корпусов")
                            )
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код таблицы корпусов"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание таблицы корпусов'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Таблица корпусов')
        verbose_name_plural = _('Таблица корпусов для их логического объединения для групповой обработки')

    def __str__(self) :
        return self.name

    @property
    def related_bodies_display(self) :
        """Отображает связанные корпуса"""
        bodies = self.model_body_body_table.all()
        if bodies :
            return ", ".join([f"{body.name}" for body in bodies])
        return _("Нет связанных моделей корпусов")

    related_bodies_display.fget.short_description = _('Связанные модели корпуса')


class PneumaticActuatorBody(models.Model) :
    """
    Корпус привода - DA или SR - у них есть или нет пружины, могут быть разное количество пружин
    Для каждого корпуса уникальны
        размеры
        площадка
        квадрат
        отверстия под пневмо
        объем цилиндра
    общей является принадлежность к какой-то серии пневмоприводов - в серии описываются
    общие для всех моделей параметры
    это model_line
    """
    name = models.CharField(max_length=100 , blank=True , null=True ,
                            verbose_name=_("Название") ,
                            help_text=_("Название модели корпуса привода")
                            )
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код модели корпуса привода"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели корпуса привода'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    body_table = models.ForeignKey(PneumaticActuatorBodyTable , on_delete=models.PROTECT ,
                                   verbose_name=_("Таблица") ,
                                   related_name='model_body_body_table' ,
                                   help_text=_(
                                       'Таблица корпусов для их логического объединения для групповой обработки'))
    mounting_plate = models.ManyToManyField(MountingPlateTypes , blank=True ,
                                            related_name='model_body_mounting_plate_pneumatic_model_line' ,
                                            verbose_name=_("Монт.площадка") ,
                                            help_text=_('Монтажная площадка'))
    stem_shape = models.ForeignKey(StemShapes , on_delete=models.SET_NULL , null=True , blank=True ,
                                   related_name='model_body_stem_shape_pneumatic_model_line' ,
                                   verbose_name=_("Тип штока") ,
                                   help_text=_('Тип отверстия под шток арматуры'))
    stem_size = models.ForeignKey(StemSize , on_delete=models.SET_NULL , null=True , blank=True ,
                                  related_name='model_body_stem_size_pneumatic_model_line' ,
                                  verbose_name=_("Размер штока") ,
                                  help_text=_('Размер отверстия под шток арматуры'))
    max_stem_height = models.PositiveIntegerField(blank=True , null=True ,
                                                  verbose_name=_("Высота штока") ,
                                                  help_text=_('Глубина отверстия под шток арматуры'))
    max_stem_diameter = models.PositiveIntegerField(blank=True , null=True ,
                                                    verbose_name=_("Макс шток") ,
                                                    help_text=_('Максимальный диаметр отверстия '
                                                                'под шток арматуры'))
    min_pressure_bar = models.DecimalField(max_digits=4 , decimal_places=1 ,
                                           default=2.5 , blank=True , null=True ,
                                           verbose_name=_("Мин давление, бар") ,
                                           help_text=_(
                                               'Давление удержания: минимальное давление необходимое для работы привода, бар'))
    max_pressure_bar = models.DecimalField(max_digits=4 , decimal_places=1 ,
                                           default=2.5 , blank=True , null=True ,
                                           verbose_name=_("Макс давление, бар") ,
                                           help_text=_(
                                               'Максимальное допустимое давление для работы привода, бар'))
    air_usage_open = models.DecimalField(max_digits=10 , decimal_places=2 ,
                                         blank=True , null=True ,
                                         verbose_name=_("Расход откр, л'") ,
                                         help_text=_(
                                             'Расход воздуха пневмоприводом за цикл открытия, л'))
    air_usage_close = models.DecimalField(max_digits=4 , decimal_places=2 ,
                                          blank=True , null=True ,
                                          verbose_name=_("Расход закр, л'") ,
                                          help_text=_(
                                              'Расход воздуха пневмоприводом за цикл закрытия, л'))
    piston_diameter = models.DecimalField(max_digits=4 , decimal_places=1 ,
                                          default=0 , blank=True , null=True ,
                                          verbose_name=_("Поршень") ,
                                          help_text=_(
                                              'Диаметр поршня, мм'))
    turn_angle = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Угол поворота") ,
                                  help_text=_("Угол поворота"))
    turn_tuning_limit = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Ограничитель") ,
                                         help_text=_("Настройка ограничителя на ±1° (об.)"))
    weight_spring = models.DecimalField(max_digits=4 , decimal_places=2 ,
                                        default=0 , blank=True , null=True ,
                                        verbose_name=_("Вес пружины") ,
                                        help_text=_(
                                            'Вес 1 пружины, кг'))

    thread_in = models.ForeignKey(ThreadSize , on_delete=models.SET_NULL , null=True , blank=True ,
                                  related_name='model_body_thread_in' ,
                                  verbose_name=_("Пневмовход") ,
                                  help_text=_('Резьба входного отверстия для пневмоподключения'))
    thread_out = models.ForeignKey(ThreadSize , on_delete=models.SET_NULL , null=True , blank=True ,
                                   related_name='model_body_thread_out' ,
                                   verbose_name=_("Пневмовыход") ,
                                   help_text=_('Резьба выходного отверстия для пневмоподключения'))
    pneumatic_connection = models.ManyToManyField(
        PneumaticConnection ,
        blank=True ,
        related_name='model_body_pneumatic_connection' ,
        verbose_name=_("Пневмоподключения") ,
        help_text=_('Возможные типы пневмоподключений'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Модель корпуса пневмопривода')
        verbose_name_plural = _('Модели корпусов пневмоприводов')

    def __str__(self) :
        return self.name


    @property
    def mounting_plate_display(self) :
        """Отображает монтажные площадки через разделитель /"""
        plates = self.mounting_plate.all()
        if plates :
            return " / ".join([str(plate) for plate in plates])
        return "-"

    mounting_plate_display.fget.short_description = _('Площадка')

    @property
    def stem_info_display(self) :
        """Отображает информацию о штоке"""
        info = []
        if self.stem_shape :
            info.append(str(self.stem_shape))
        if self.stem_size :
            info.append(str(self.stem_size))
        if self.max_stem_height :
            info.append(f"высота: {self.max_stem_height}мм")
        if self.max_stem_diameter :
            info.append(f"∅: {self.max_stem_diameter}мм")
        return " | ".join(info) if info else "-"

    stem_info_display.fget.short_description = _('Шток')

    def create_copy(self , name_suffix=None , code_suffix=None) :
        """Создает копию модели со всеми связанными данными"""
        if name_suffix is None :
            name_suffix = _(" (Копия)")
        if code_suffix is None :
            code_suffix = _(" (Копия)")

        # Сохраняем исходные отношения
        mounting_plates = list(self.mounting_plate.all())
        pneumatic_connections = list(self.pneumatic_connection.all())

        # Создаем новый объект с теми же данными
        copy = PneumaticActuatorBody(
            name=f"{self.name}{name_suffix}" if self.name else "Копия" ,
            code=f"{self.code}{code_suffix}" if self.code else "Копия" ,
            description=self.description ,
            sorting_order=self.sorting_order ,
            is_active=self.is_active ,
            body_table=self.body_table ,
            stem_shape=self.stem_shape ,
            stem_size=self.stem_size ,
            max_stem_height=self.max_stem_height ,
            max_stem_diameter=self.max_stem_diameter ,
            min_pressure_bar=self.min_pressure_bar ,
            max_pressure_bar=self.max_pressure_bar ,
            air_usage_open=self.air_usage_open ,
            air_usage_close=self.air_usage_close ,
            piston_diameter=self.piston_diameter ,
            turn_angle=self.turn_angle ,
            turn_tuning_limit=self.turn_tuning_limit ,
            weight_spring=self.weight_spring ,
            thread_in=self.thread_in ,
            thread_out=self.thread_out ,
        )
        copy.save()

        # Копируем ManyToMany поля
        copy.mounting_plate.set(mounting_plates)
        copy.pneumatic_connection.set(pneumatic_connections)

        return copy

    def get_description_data(self) -> Dict[str , Dict[str , Any]] :
        """Получить унифицированную структуру данных для описания корпуса в виде словаря"""

        return {
            # ==================== БАЗОВАЯ ИНФОРМАЦИЯ ====================
            'name' : {
                'category' : 'basic' ,
                'title' : 'Модель корпуса' ,
                'data' : self.name ,
                'display_data' : self.name if self.name else 'Не указано' ,
                'text_data' : f"Модель корпуса: {self.name}" if self.name else None
            } ,
            'code' : {
                'category' : 'basic' ,
                'title' : 'Код' ,
                'data' : self.code ,
                'display_data' : self.code if self.code else 'Не указано' ,
                'text_data' : f"Код: {self.code}" if self.code else None
            } ,
            'description' : {
                'category' : 'basic' ,
                'title' : 'Описание' ,
                'data' : self.description ,
                'display_data' : self.description if self.description else 'Не указано' ,
                'text_data' : f"Описание: {self.description}" if self.description else None
            } ,

            # ==================== ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ ====================
            'piston_diameter' : {
                'category' : 'technical' ,
                'title' : 'Диаметр поршня' ,
                'data' : self.piston_diameter ,
                'display_data' : f"{self.piston_diameter} мм" if self.piston_diameter else 'Не указано' ,
                'text_data' : f"Диаметр поршня: {self.piston_diameter} мм" if self.piston_diameter else None
            } ,
            'turn_angle' : {
                'category' : 'technical' ,
                'title' : 'Угол поворота' ,
                'data' : self.turn_angle ,
                'display_data' : self.turn_angle if self.turn_angle else 'Не указано' ,
                'text_data' : f"Угол поворота: {self.turn_angle}" if self.turn_angle else None
            } ,
            'turn_tuning_limit' : {
                'category' : 'technical' ,
                'title' : 'Ограничитель поворота' ,
                'data' : self.turn_tuning_limit ,
                'display_data' : self.turn_tuning_limit if self.turn_tuning_limit else 'Не указано' ,
                'text_data' : f"Ограничитель поворота: {self.turn_tuning_limit}" if self.turn_tuning_limit else None
            } ,
            'weight_spring' : {
                'category' : 'technical' ,
                'title' : 'Вес пружины' ,
                'data' : self.weight_spring ,
                'display_data' : f"{self.weight_spring} кг" if self.weight_spring else 'Не указано' ,
                'text_data' : f"Вес пружины: {self.weight_spring} кг" if self.weight_spring else None
            } ,
            'min_pressure' : {
                'category' : 'technical' ,
                'title' : 'Минимальное давление' ,
                'data' : self.min_pressure_bar ,
                'display_data' : f"{self.min_pressure_bar} бар" if self.min_pressure_bar else 'Не указано' ,
                'text_data' : f"Минимальное давление: {self.min_pressure_bar} бар" if self.min_pressure_bar else None
            } ,
            'max_pressure' : {
                'category' : 'technical' ,
                'title' : 'Максимальное давление' ,
                'data' : self.max_pressure_bar ,
                'display_data' : f"{self.max_pressure_bar} бар" if self.max_pressure_bar else 'Не указано' ,
                'text_data' : f"Максимальное давление: {self.max_pressure_bar} бар" if self.max_pressure_bar else None
            } ,
            'air_usage_open' : {
                'category' : 'technical' ,
                'title' : 'Расход воздуха (открытие)' ,
                'data' : self.air_usage_open ,
                'display_data' : f"{self.air_usage_open} л" if self.air_usage_open else 'Не указано' ,
                'text_data' : f"Расход воздуха (открытие): {self.air_usage_open} л" if self.air_usage_open else None
            } ,
            'air_usage_close' : {
                'category' : 'technical' ,
                'title' : 'Расход воздуха (закрытие)' ,
                'data' : self.air_usage_close ,
                'display_data' : f"{self.air_usage_close} л" if self.air_usage_close else 'Не указано' ,
                'text_data' : f"Расход воздуха (закрытие): {self.air_usage_close} л" if self.air_usage_close else None
            } ,

            # ==================== ШТОК ====================
            'stem_shape' : {
                'category' : 'stem' ,
                'title' : 'Форма штока' ,
                'data' : self.stem_shape ,
                'display_data' : str(self.stem_shape) if self.stem_shape else 'Не указано' ,
                'text_data' : f"Форма штока: {self.stem_shape}" if self.stem_shape else None
            } ,
            'stem_size' : {
                'category' : 'stem' ,
                'title' : 'Размер штока' ,
                'data' : self.stem_size ,
                'display_data' : str(self.stem_size) if self.stem_size else 'Не указано' ,
                'text_data' : f"Размер штока: {self.stem_size}" if self.stem_size else None
            } ,
            'max_stem_height' : {
                'category' : 'stem' ,
                'title' : 'Макс. высота штока' ,
                'data' : self.max_stem_height ,
                'display_data' : f"{self.max_stem_height} мм" if self.max_stem_height else 'Не указано' ,
                'text_data' : f"Макс. высота штока: {self.max_stem_height} мм" if self.max_stem_height else None
            } ,
            'max_stem_diameter' : {
                'category' : 'stem' ,
                'title' : 'Макс. диаметр штока' ,
                'data' : self.max_stem_diameter ,
                'display_data' : f"{self.max_stem_diameter} мм" if self.max_stem_diameter else 'Не указано' ,
                'text_data' : f"Макс. диаметр штока: {self.max_stem_diameter} мм" if self.max_stem_diameter else None
            } ,

            # ==================== МОНТАЖНЫЕ ПЛОЩАДКИ ====================
            'mounting_plates' : {
                'category' : 'mounting' ,
                'title' : 'Монтажные площадки' ,
                'data' : [str(plate) for plate in self.mounting_plate.all()] if self.mounting_plate.exists() else None ,
                'display_data' : ', '.join([str(plate) for plate in
                                            self.mounting_plate.all()]) if self.mounting_plate.exists() else 'Не указано' ,
                'text_data' : f"Монтажные площадки: {', '.join([str(plate) for plate in self.mounting_plate.all()])}" if self.mounting_plate.exists() else None
            } ,

            # ==================== ПОДКЛЮЧЕНИЯ ====================
            'thread_in' : {
                'category' : 'pipe_connections' ,
                'title' : 'Пневмовход' ,
                'data' : self.thread_in ,
                'display_data' : str(self.thread_in) if self.thread_in else 'Не указано' ,
                'text_data' : f"Пневмовход: {self.thread_in}" if self.thread_in else None
            } ,
            'thread_out' : {
                'category' : 'pipe_connections' ,
                'title' : 'Пневмовыход' ,
                'data' : self.thread_out ,
                'display_data' : str(self.thread_out) if self.thread_out else 'Не указано' ,
                'text_data' : f"Пневмовыход: {self.thread_out}" if self.thread_out else None
            } ,
            'pneumatic_connections' : {
                'category' : 'pipe_connections' ,
                'title' : 'Типы пневмоподключений' ,
                'data' : [str(conn) for conn in
                          self.pneumatic_connection.all()] if self.pneumatic_connection.exists() else None ,
                'display_data' : ', '.join([str(conn) for conn in
                                            self.pneumatic_connection.all()]) if self.pneumatic_connection.exists() else 'Не указано' ,
                'text_data' : f"Типы пневмоподключений: {', '.join([str(conn) for conn in self.pneumatic_connection.all()])}" if self.pneumatic_connection.exists() else None
            } ,
        }

    def get_text_description(self) -> str :
        """Сгенерировать текстовое описание корпуса"""
        data = self.get_description_data()
        lines = []

        # Обходим все параметры
        for key , param in data.items() :
            if param.get('text_data') :
                lines.append(param['text_data'])

        return "\n".join(lines)

    def get_display_list(self , category: str = None) -> List[tuple] :
        """Получить список для отображения (title, display_data) с фильтром по категории"""
        data = self.get_description_data()
        result = []

        for key , param in data.items() :
            if category and param.get('category') != category :
                continue
            result.append((param['title'] , param['display_data']))

        return result

    @property
    def full_description(self) -> str :
        """Полное описание корпуса (property)"""
        return self.get_text_description()

class PneumaticWeightParameter(models.Model) :
    """Вес пневмопривода зависит от корпуса и количества пружин
        Здесь мы прописываем этот вес в зависимости от количества пружин
        spring_qty - количество прудин или DA"""
    body = models.ForeignKey(PneumaticActuatorBody , on_delete=models.CASCADE ,
                             related_name='pa_weight_parameter' ,
                             verbose_name=_("Модель") ,
                             help_text=_("Модель корпуса привода"))
    spring_qty = models.ForeignKey('pneumatic_actuators.PneumaticActuatorSpringsQty' , on_delete=models.SET_NULL ,
                                   null=True , blank=True ,  # ← ДОБАВЬТЕ ЭТО
                                   related_name='pa_weight_parameter' ,
                                   verbose_name=_("Пружин / DA") ,
                                   help_text=_("Количество пружин или DA"))
    weight = models.DecimalField(max_digits=10 , decimal_places=2 ,
                                 default=0.0 , verbose_name=_("Вес, кг") ,
                                 help_text=_("Вес корпуса привода с кол-вом пружин или DA"))

    class Meta :
        verbose_name = _("Вес пневмопривода")
        verbose_name_plural = _("Вес пневмоприводов")
        ordering = ['spring_qty']
        unique_together = ['body' , 'spring_qty']

    def __str__(self) :
        return f"Вес {self.body.name} - {self.spring_qty.name}"


class PneumaticCloseTimeParameter(models.Model) :
    """Время открытия пневмопривода зависит от размера корпуса и количества пружин
        Здесь мы прописываем этот вес в зависимости от количества пружин
        spring_qty - количество прудин или DA"""
    body = models.ForeignKey(PneumaticActuatorBody , on_delete=models.CASCADE ,
                             related_name='pa_close_time_parameter' ,
                             verbose_name=_("Модель") ,
                             help_text=_("Модель корпуса привода"))
    spring_qty = models.ForeignKey('pneumatic_actuators.PneumaticActuatorSpringsQty' , on_delete=models.SET_NULL ,
                                   null=True , blank=True ,  # ← ДОБАВЬТЕ ЭТО
                                   related_name='pa_close_time_parameter' ,
                                   verbose_name=_("Пружин / DA") ,
                                   help_text=_("Количество пружин или DA"))
    pressure = models.ForeignKey('params.PneumaticAirSupplyPressure',
                                 on_delete=models.SET_DEFAULT,
                                 default=13,  # ID записи с давлением 6 бар
                                 verbose_name=_("Давление питания"),
                                 help_text=_("Давление в пневмосистеме, бар"))
    time_close = models.DecimalField(max_digits=4 , decimal_places=2 ,
                                     default=0.0 , verbose_name=_("Закрытие, сек") ,
                                     help_text=_("Время закрытия пневмопривода с кол-вом пружин или DA, секунд"))
    time_open = models.DecimalField(max_digits=4 , decimal_places=2 ,
                                    default=0.0 , verbose_name=_("Открытие, сек") ,
                                    help_text=_("Время открытия пневмопривода с кол-вом пружин или DA, секунд"))

    class Meta :
        verbose_name = _("Время открытия/закрытия пневмопривода")
        verbose_name_plural = _("Время открытия/закрытия пневмоприводов")
        ordering = ['spring_qty']
        unique_together = ['body' , 'spring_qty']

    def __str__(self) :
        return f"Время откр/закр {self.spring_qty.name}:{self.time_open}/{self.time_close} сек"

    @classmethod
    def get_time_to_close(cls, body_id, spring_da, pressure=None):
        """
        Получить время открытия/закрытия для пневмопривода
        """
        from pneumatic_actuators.models import PneumaticActuatorSpringsQty
        from params.models import PneumaticAirSupplyPressure
        from pneumatic_actuators.services.pneumatic_calculator import PneumaticCalculator
        from django.db import models

        # Определяем тип и целевые параметры
        is_da = False
        target_springs_qty = None
        target_pressure_bar = None

        # Разбираем spring_da
        if isinstance(spring_da, PneumaticActuatorSpringsQty):
            spring_code = spring_da.code
            is_da = (spring_code == 'DA')
            if not is_da:
                try:
                    target_springs_qty = int(spring_code)
                except (ValueError, TypeError):
                    target_springs_qty = None
        elif isinstance(spring_da, int):
            try:
                spring_obj = PneumaticActuatorSpringsQty.objects.get(id=spring_da)
                spring_code = spring_obj.code
                is_da = (spring_code == 'DA')
                if not is_da:
                    try:
                        target_springs_qty = int(spring_code)
                    except (ValueError, TypeError):
                        target_springs_qty = None
            except PneumaticActuatorSpringsQty.DoesNotExist:
                return None
        else:
            spring_code = str(spring_da)
            is_da = (spring_code == 'DA')
            if not is_da:
                try:
                    target_springs_qty = int(spring_code)
                except (ValueError, TypeError):
                    target_springs_qty = None

        # Разбираем pressure
        pressure_id = None
        if pressure is not None:
            if isinstance(pressure, PneumaticAirSupplyPressure):
                pressure_id = pressure.id
                target_pressure_bar = float(pressure.pressure_bar)
            elif isinstance(pressure, (int, float)):
                target_pressure_bar = float(pressure)
                pressure_obj = PneumaticAirSupplyPressure.objects.filter(pressure_bar=target_pressure_bar).first()
                pressure_id = pressure_obj.id if pressure_obj else None
            elif isinstance(pressure, str):
                if pressure.isdigit():
                    pressure_id = int(pressure)
                    pressure_obj = PneumaticAirSupplyPressure.objects.filter(id=pressure_id).first()
                    if pressure_obj:
                        target_pressure_bar = float(pressure_obj.pressure_bar)
                else:
                    pressure_obj = PneumaticAirSupplyPressure.objects.filter(
                        models.Q(name=pressure) | models.Q(code=pressure)
                    ).first()
                    if pressure_obj:
                        pressure_id = pressure_obj.id
                        target_pressure_bar = float(pressure_obj.pressure_bar)

        # Формируем базовый запрос
        queryset = cls.objects.filter(body_id=body_id)

        if is_da:
            queryset = queryset.filter(spring_qty__code='DA')
        else:
            queryset = queryset.exclude(spring_qty__code='DA')

        # Пытаемся найти точное совпадение
        if pressure_id:
            exact_match = queryset.filter(pressure_id=pressure_id).select_related('spring_qty', 'pressure',
                                                                                  'body').first()
            if exact_match:
                # Получаем объем цилиндра
                volume_liters = getattr(exact_match.body, 'air_usage_open', None)
                if volume_liters is None and exact_match.body.piston_diameter:
                    # Если нет расхода, рассчитываем приблизительно
                    piston_diameter_m = float(exact_match.body.piston_diameter) / 1000
                    area_m2 = 3.14159 * (piston_diameter_m / 2) ** 2
                    stroke_m = piston_diameter_m * 0.8
                    volume_m3 = area_m2 * stroke_m
                    volume_liters = volume_m3 * 1000

                air_consumption = None
                if volume_liters:
                    air_consumption = PneumaticCalculator.calculate_air_consumption(
                        pressure_bar=float(exact_match.pressure.pressure_bar),
                        volume_liters=float(volume_liters),
                        is_da=is_da
                    )

                return {
                    'time_open': float(exact_match.time_open),
                    'time_close': float(exact_match.time_close),
                    'pressure_bar': float(exact_match.pressure.pressure_bar),
                    'calculated': False,
                    'has_calculated_values': False,
                    'calculated_time_open': None,
                    'calculated_time_close': None,
                    'calculated_pressure_bar': None,
                    'calculated_springs_qty': None,
                    'base_pressure': None,
                    'base_springs_qty': None,
                    'air_consumption': air_consumption,
                    'can_operate': True,
                    'error': None,
                }

        # Если точного совпадения нет, берем любую запись для этого body_id и типа привода
        base_record = queryset.select_related('spring_qty', 'pressure', 'body').first()

        if not base_record:
            return None

        # Формируем базовую запись для расчета
        # Это та запись, которую мы нашли в БД (с любым давлением и количеством пружин)

        # Если нет целевого давления, берем из базовой записи
        if target_pressure_bar is None:
            target_pressure_bar = float(base_record.pressure.pressure_bar)

        # Если нет целевого количества пружин для SR, берем из базовой записи
        if not is_da and target_springs_qty is None:
            if base_record.spring_qty and base_record.spring_qty.code != 'DA':
                try:
                    target_springs_qty = int(base_record.spring_qty.code)
                except (ValueError, TypeError):
                    target_springs_qty = 0
            else:
                target_springs_qty = 0

        # Базовые значения для расчета (из найденной записи)
        base_pressure = float(base_record.pressure.pressure_bar)
        base_time_open = float(base_record.time_open)
        base_time_close = float(base_record.time_close)

        base_springs_qty = 0
        if base_record.spring_qty and base_record.spring_qty.code != 'DA':
            try:
                base_springs_qty = int(base_record.spring_qty.code)
            except (ValueError, TypeError):
                base_springs_qty = 0

        # Для расчета сопротивления пружин нужна запись DA для этого же корпуса
        da_record = cls.objects.filter(
            body_id=body_id,
            spring_qty__code='DA'
        ).select_related('pressure').first()

        if da_record:
            base_p_da = float(da_record.pressure.pressure_bar)
            base_t_open_da = float(da_record.time_open)
        else:
            # Если нет записи DA, используем приблизительные коэффициенты
            base_p_da = base_pressure
            base_t_open_da = base_time_open * 1.6 if not is_da else base_time_open

        # Получаем геометрические параметры из модели body
        piston_diameter = getattr(base_record.body, 'piston_diameter', None)

        # Получаем объем цилиндра из расхода воздуха (или рассчитываем)
        air_usage_open = getattr(base_record.body, 'air_usage_open', None)

        if air_usage_open is not None and air_usage_open > 0:
            volume_liters = float(air_usage_open)
        elif piston_diameter is not None and piston_diameter > 0:
            # Рассчитываем объем приблизительно
            try:
                piston_diameter_m = float(piston_diameter) / 1000
                area_m2 = 3.14159 * (piston_diameter_m / 2) ** 2
                stroke_m = piston_diameter_m * 0.8  # ход ≈ 80% от диаметра
                volume_m3 = area_m2 * stroke_m
                volume_liters = volume_m3 * 1000
                volume_liters = round(volume_liters, 4)
            except (ValueError, TypeError):
                volume_liters = None
        else:
            volume_liters = None

        # Проверяем наличие обязательных параметров для расчета
        if piston_diameter is None or volume_liters is None:
            # Если расчета нет, возвращаем известные значения из базовой записи
            return {
                'time_open': base_time_open,
                'time_close': base_time_close,
                'pressure_bar': base_pressure,
                'calculated': False,
                'has_calculated_values': False,
                'calculated_time_open': None,
                'calculated_time_close': None,
                'calculated_pressure_bar': None,
                'calculated_springs_qty': None,
                'base_pressure': base_pressure,
                'base_springs_qty': base_springs_qty,
                'target_pressure_bar': target_pressure_bar,
                'target_springs_qty': target_springs_qty if not is_da else 0,
                'error': f"Cannot calculate: missing geometric data for body_id={body_id}. Using base values.",
                'can_operate': None,
            }

        # Конвертируем в float
        try:
            piston_diameter = float(piston_diameter)
            volume_liters = float(volume_liters)
        except (TypeError, ValueError) as e:
            # При ошибке конвертации тоже возвращаем базовые значения
            return {
                'time_open': base_time_open,
                'time_close': base_time_close,
                'pressure_bar': base_pressure,
                'calculated': False,
                'has_calculated_values': False,
                'calculated_time_open': None,
                'calculated_time_close': None,
                'calculated_pressure_bar': None,
                'calculated_springs_qty': None,
                'base_pressure': base_pressure,
                'base_springs_qty': base_springs_qty,
                'target_pressure_bar': target_pressure_bar,
                'target_springs_qty': target_springs_qty if not is_da else 0,
                'error': f"Invalid geometric data: {e}. Using base values.",
                'can_operate': None,
            }

        # Выполняем физический расчет
        from pneumatic_actuators.services.pneumatic_calculator import PneumaticCalculator

        result = PneumaticCalculator.calculate_actuator_data(
            mechanism_type='rack_pinion',
            is_target_sr=not is_da,
            target_pressure_bar=target_pressure_bar,
            target_springs_qty=target_springs_qty if not is_da else 0,
            base_p_sr=base_pressure,
            base_t_open_sr=base_time_open,
            base_t_close_sr=base_time_close,
            base_springs_qty=base_springs_qty,
            base_p_da=base_p_da,
            base_t_open_da=base_t_open_da,
            piston_diameter=piston_diameter,
            volume_liters=volume_liters,
            valve_torque_nm=0
        )

        if result:
            return {
                'time_open': result['time_open_sec'],
                'time_close': result['time_close_sec'],
                'pressure_bar': target_pressure_bar,
                'calculated': True,
                'has_calculated_values': True,
                'calculated_time_open': result['time_open_sec'],
                'calculated_time_close': result['time_close_sec'],
                'calculated_pressure_bar': target_pressure_bar,
                'calculated_springs_qty': target_springs_qty if not is_da else 0,
                'base_pressure': base_pressure,
                'base_springs_qty': base_springs_qty,
                'air_consumption': result.get('air_consumption_norm_liters'),
                'can_operate': result.get('can_operate'),
                'p_loss_springs': result.get('p_loss_springs_bar'),
                'p_loss_valve': result.get('p_loss_valve_bar'),
                'error': None,
            }

        # Если расчет не удался, возвращаем базовые значения
        return {
            'time_open': base_time_open,
            'time_close': base_time_close,
            'pressure_bar': base_pressure,
            'calculated': False,
            'has_calculated_values': False,
            'calculated_time_open': None,
            'calculated_time_close': None,
            'calculated_pressure_bar': None,
            'calculated_springs_qty': None,
            'base_pressure': base_pressure,
            'base_springs_qty': base_springs_qty,
            'target_pressure_bar': target_pressure_bar,
            'target_springs_qty': target_springs_qty if not is_da else 0,
            'error': 'Calculation failed. Using base values.',
            'can_operate': None,
        }