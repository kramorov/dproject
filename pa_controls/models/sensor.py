from typing import Dict

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import TemplateMixin, GetChoicesMixin, CopyMixin
# from pa_controls.models import LimitSwitchSensorVariety, SignalType, ContactForm, ContactState
from producers.models import Brands


class SensorComponent(TemplateMixin, GetChoicesMixin, CopyMixin, models.Model):
    """База данных конкретных моделей датчиков и трансмиттеров"""
    name = models.CharField(max_length=200,
        verbose_name=_("Название"),
        help_text=_('Текстовое название модели датчика'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код модели датчика"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание модели датчика'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    brand = models.ForeignKey(Brands, related_name='sensor_component_brand', blank=True, null=True,
                              on_delete=models.SET_NULL,
                              help_text=_('Бренд'),
                              verbose_name=_("Бренд датчика"))
    # Ссылки на созданные ранее справочники
    variety = models.ForeignKey('pa_controls.LimitSwitchSensorVariety', on_delete=models.PROTECT, verbose_name=_("Тип сенсора"))
    signal_type = models.ForeignKey('pa_controls.SignalType', on_delete=models.PROTECT, verbose_name=_("Тип сигнала"))
    contact_form = models.ForeignKey('pa_controls.ContactForm', on_delete=models.PROTECT, verbose_name=_("Форма контактов"))
    contact_state = models.ForeignKey('pa_controls.ContactState', on_delete=models.PROTECT, verbose_name=_("Состояние контакта"))

    # Электрические параметры строкой (как в паспорте)
    electrical_specs = models.CharField(
        max_length=255,
        verbose_name=_("Электрические характеристики"),
        help_text=_("Например: '8.2В / 25мА' или '250В (AC) / 1.0А' или '24В / 4-20мА'")
    )

    wires_count = models.PositiveSmallIntegerField(
        default=2,
        verbose_name=_("Кол-во проводов"),
        help_text=_("Фактическое количество жил для подключения этого датчика")
    )

    # Искробезопасные параметры (отдельные поля для расчетов)
    ui = models.FloatField(null=True, blank=True, verbose_name=_("Ui (В)"), help_text=_('Максимальное входное напряжение Ui (В): Это предел напряжения, который может быть подан на устройство без нарушения его искробезопасности. Если стоит 0, значит, прибор не сертифицирован как «искробезопасный аппарат».'))
    ii = models.FloatField(null=True, blank=True, verbose_name=_("Ii (мА)"), help_text=_('Максимальный входной ток Ii (мА): Максимальный ток, который может выдержать внутренняя схема датчика при сохранении безопасности.'))
    pi = models.FloatField(null=True, blank=True, verbose_name=_("Pi (мВт)"), help_text=_('Максимальная входная мощность Pi (мВт): Лимит мощности, которую устройство может рассеивать, чтобы не вызвать воспламенение окружающей среды.'))
    ci = models.FloatField(null=True, blank=True, verbose_name=_("Ci (нФ)"), help_text=_('Внутренняя емкость Ci (нФ): Суммарная емкость всех компонентов внутри датчика. При проектировании систем автоматики её учитывают вместе с емкостью кабеля, чтобы избежать накопления энергии.'))
    li = models.FloatField(null=True, blank=True, verbose_name=_("Li (мкГн)"), help_text=_('Внутренняя индуктивность Li (мкГн): Суммарная индуктивность датчика. Её учитывают для предотвращения искрового разряда при размыкании цепи.'))
    # Ui(В): {ui}, Ii (мА):{ii}, Pi (мВт):{pi}, Li (мкГн):{li}
    # Всё остальное (материалы, частота, гистерезис, SIL, МДС)
    extra_params = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Дополнительные параметры"),
        help_text=_("Специфические данные: материал, частота, SIL, МДС, погрешность и т.д.")
    )

    class Meta:
        verbose_name = _("Датчик (компонент)")
        verbose_name_plural = _("Датчики (компоненты)")

    def __str__(self):
        return f"{self.name}"

    @property
    def get_exi_params(self):
        exi_template="Максимальное входное напряжение Ui(В): {ui}, Максимальный входной ток Ii(мА): {ii}, Максимальная входная мощность Pi(мВт): {pi}, Внутренняя емкость Ci (нФ): {ci}, Внутренняя индуктивность Li(мкГн): {li}"
        # Временно сохраняем оригинальные значения
        # и создаем словарь только с нужными полями

        # Получаем значения и преобразуем в float (None -> 0)
        def safe_float(val):
            try:
                return float(val) if val not in (None, '') else 0.0
            except (ValueError, TypeError):
                return 0.0

        values = [safe_float(self._get_value(field)) for field in ['ui', 'ii', 'pi', 'ci', 'li']]

        if any(v != 0 for v in values):
            # Используем существующий метод
            return self._fill_template(exi_template,self._get_data_dict())
        else:
            return "Датчик не является искробезопасным электрооборудованием и не требует использования барьеров искрозащиты"

    @property
    def get_brand_name(self):
        return self.brand.name if self.brand else "OEM"

    def _get_data_dict(self) -> Dict[str , str] :
        """
        Словарь соответствий плейсхолдеров и путей к атрибутам для SensorComponent
        """
        return {
            # Основные поля
            '{model_code}' : 'code' ,
            '{name}' : 'name' ,
            '{brand}' : 'get_brand_name',
            # Тип сенсора (sensor_variety)
            '{sensor_variety}' : 'variety__name' ,
            # Тип сигнала
            '{signal_type}' : 'signal_type__name' ,
            # Форма контактов
            '{contact_form}' : 'contact_form__name' ,
            '{contact_form_code}': 'contact_form__code',
            # Состояние контакта
            '{contact_state}' : 'contact_state__name' ,
            # Электрические параметры
            '{electrical_specs}' : 'electrical_specs' ,
            '{wires_count}' : 'wires_count' ,
            # Искробезопасные параметры
            '{ui}' : 'ui' ,
            '{ii}' : 'ii' ,
            '{pi}' : 'pi' ,
            '{ci}' : 'ci' ,
            '{li}' : 'li' ,
            '{exi_params}' : 'get_exi_params',
            '{extra_params}': 'get_extra_params',
            # JSON параметры (через .)
            # '{material}' : 'extra_params.material' ,
            # '{frequency}' : 'extra_params.frequency' ,
            # '{hysteresis}' : 'extra_params.hysteresis' ,
            # '{sil}' : 'extra_params.sil' ,
            # '{mds}' : 'extra_params.mds' ,
            # '{accuracy}' : 'extra_params.accuracy' ,
            # '{temperature_drift}' : 'extra_params.temperature_drift' ,
            # '{response_time}' : 'extra_params.response_time' ,
            # '{certification}' : 'extra_params.certification' ,
        }
    def _get_name_template_source(self):
        """Переопределить в модели: вернуть шаблон названия или None."""
        return self.variety.name_template or None

    def _get_description_template_source(self):
        """Переопределить в модели: вернуть шаблон описания или None."""
        return self.variety.description_template or None

    def _get_default_name_template(self) -> str :
        """Шаблон названия по умолчанию"""
        return self.variety.name_template if self.variety else None

    def _get_default_description_template(self) -> str :
        """Шаблон описания по умолчанию"""
        # Искробезопасность: Ui={ui}В Ii={ii}мА Pi={pi}мВт Ci={ci}нФ Li={li}мкГн. Материал: {material}, частота: {frequency}, SIL: {sil}"
        return self.variety.description_template if self.variety else None

    def save(self, *args, **kwargs):
        # skip_auto_generate = kwargs.pop('skip_auto_generate', False)
        print(f'save from SenSorComponent')
        self.update_description()
        super().save(skip_auto_generate=True, *args, **kwargs)
