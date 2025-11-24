# pneumatic_actuators/models/pa_body.py

from django.db import models
from django.utils.translation import gettext_lazy as _
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
