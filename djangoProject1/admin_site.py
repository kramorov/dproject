# djangoProject1/admin_site.py
"""Кастомный AdminSite: главная страница админки сгруппирована по логическим разделам.

Как это работает:
  * ADMIN_BLOCKS — упорядоченный список разделов (id, заголовок, описание).
  * ADMIN_MODEL_BLOCK — словарь соответствия ('app_label', 'ObjectName') -> id раздела.
  * Модели, которых нет в словаре, автоматически попадают в раздел «Новые модели»
    (id 'new', показывается только если непустой) — перенесите их вручную в нужный
    раздел, добавив запись в ADMIN_MODEL_BLOCK.

Как добавить раздел: добавьте кортеж в ADMIN_BLOCKS в нужном месте списка
(порядок в списке = порядок на странице).

Реестр ModelAdmin'ов переносится из admin.site целиком (см. grouped_admin_site
внизу) — все страницы моделей, инлайны, действия и права остаются прежними;
меняется только главная страница /admin/.

Подключение: djangoProject1/urls.py использует grouped_admin_site.urls.
"""

from django.contrib import admin
from django.contrib.admin import AdminSite
import logging

# ---------------------------------------------------------------------------
# Разделы главной страницы (порядок = порядок отображения)
# ---------------------------------------------------------------------------
ADMIN_BLOCKS = [
    # --- Продуктовые линейки ---
    ('valves', 'Арматура',
     'Серии, модели, таблицы данных и ВГХ трубопроводной арматуры'),
    ('electric_actuators', 'Электроприводы',
     'Серии, корпуса и модели электроприводов'),
    ('ett', 'Электроприводы: опции и БУ',
     'Справочники электроприводов: БУ, сигналы, климатика, документы'),
    ('pneumatic_actuators', 'Пневмоприводы',
     'Серии, корпуса и модели пневмоприводов'),
    ('fittings', 'Пневматические фитинги',
     'Фитинги: резьба-трубка, глушители, заглушки'),
    ('filter_regulators', 'Фильтры-регуляторы',
     'Фильтры-регуляторы сжатого воздуха'),
    ('solenoid_valves', 'Соленоидные клапаны',
     'Электромагнитные распределительные клапаны'),
    ('gearboxes', 'Редукторы',
     'Редукторы и ручные дублеры'),
    ('cable_glands', 'Кабельные вводы',
     'Кабельные вводы: корпуса, материалы, серии'),
    # --- БКВ и позиционеры ---
    ('lsb', 'БКВ (коробки)',
     'БКВ: корпуса, серии, датчики, контакты, индикаторы'),
    ('positioners', 'Позиционеры',
     'Позиционеры: серии, корпуса, рычаги, смарт-возможности'),
    # --- Сигналы и взрывозащита ---
    ('signals', 'Сигналы и профили',
     'Профили сигналов БУ, роли и спецификации входных сигналов'),
    ('ex', 'Взрывозащита (Ex)',
     'Типы, уровни и методы взрывозащиты, температурные классы, группы'),
    # --- Справочники ---
    ('threads', 'Резьбы и присоединения',
     'Резьбы, наборы резьб, присоединения, штоки, монтажные пластины'),
    ('climate', 'Климатика и степень защиты',
     'Климатическое исполнение, категории размещения, IP'),
    ('control', 'Управление и индикация',
     'Блоки управления, режимы работы, сигнальные устройства, питание'),
    ('coatings', 'Покрытия и цвета',
     'Покрытия и цвета корпуса'),
    ('dicts', 'Справочники (прочие)',
     'Общие справочники: типы арматуры, функции, герметичность, особенности'),
    ('materials', 'Материалы',
     'Материалы, стандарты, химическая стойкость, рабочие среды'),
    ('certs', 'Сертификаты',
     'Сертификаты и их виды'),
    ('media', 'Медиабиблиотека',
     'Файлы, категории, наборы галерей'),
    ('producers', 'Бренды и производители',
     'Бренды и производители'),
    ('prices', 'Цены и валюты',
     'Цены, валюты, курсы, документы, конструктор цен'),
    # --- Конфигуратор и номенклатура ---
    ('configurator', 'Конфигуратор и мастера',
     'Типы оборудования, мастера подбора, правила и параметры'),
    ('sku', 'Номенклатура (SKU / MBOM)',
     'Номенклатура SKU и спецификации MBOM'),
    # --- Клиенты и сервис ---
    ('requests', 'Заявки клиентов',
     'Заявки клиентов и корзины'),
    ('customers', 'Клиенты и доступ',
     'Клиенты, юрлица, пользователи портала, доступы'),
    ('ai', 'AI-ассистент',
     'Провайдеры, промпты, схемы, диалоги'),
    ('system', 'Система и пользователи',
     'Пользователи, группы и оформление админки'),
]

# Раздел для моделей, не привязанных к блокам (показывается только если непустой)
NEW_MODELS_BLOCK = 'new'
NEW_MODELS_TITLE = 'Новые модели'
NEW_MODELS_DESC = 'Модели без привязки к разделу — добавьте их в ADMIN_MODEL_BLOCK ' \
                  '(djangoProject1/admin_site.py).'

# ---------------------------------------------------------------------------
# Соответствие ('app_label', 'ObjectName') -> id раздела
# ---------------------------------------------------------------------------
ADMIN_MODEL_BLOCK = {
    # --- Арматура ---
    ('valve_data', 'AllowedDnTemplate'): 'valves',
    ('valve_data', 'ConstructionVariety'): 'valves',
    ('valve_data', 'PortQty'): 'valves',
    ('valve_data', 'ValveConnectionToPipe'): 'valves',
    ('valve_data', 'ValveDimensionTable'): 'valves',
    ('valve_data', 'ValveLine'): 'valves',
    ('valve_data', 'ValveModelDataTable'): 'valves',
    ('valve_data', 'ValveModelKvDataTable'): 'valves',
    ('valve_data', 'ValveVariety'): 'valves',
    ('valve_data', 'WeightDimensionParameterVariety'): 'valves',
    # --- Электроприводы ---
    ('electric_actuators', 'AllowedControlUnitOption'): 'electric_actuators',
    ('electric_actuators', 'AllowedSignalProfileOption'): 'electric_actuators',
    ('electric_actuators', 'AllowedTurnCounterOption'): 'electric_actuators',
    ('electric_actuators', 'CableGlandHolesSet'): 'electric_actuators',
    ('electric_actuators', 'ControlUnitWiring'): 'electric_actuators',
    ('electric_actuators', 'ElectricActuatorBody'): 'electric_actuators',
    ('electric_actuators', 'ElectricActuatorBodyTable'): 'electric_actuators',
    ('electric_actuators', 'ElectricActuatorConstructor'): 'electric_actuators',
    ('electric_actuators', 'ElectricActuatorData'): 'electric_actuators',
    ('electric_actuators', 'ElectricActuatorModelLine'): 'electric_actuators',
    ('electric_actuators', 'ElectricActuatorModelLineItem'): 'electric_actuators',
    ('electric_actuators', 'ElectricActuatorSelected'): 'electric_actuators',
    ('electric_actuators', 'ElectricExdOption'): 'electric_actuators',
    ('electric_actuators', 'ElectricPowerSupplyOption'): 'electric_actuators',
    ('electric_actuators', 'ModelBody'): 'electric_actuators',
    # --- Электроприводы: опции (ETT) ---
    ('ett', 'DnType'): 'ett',
    ('ett', 'EttActuatorType'): 'ett',
    ('ett', 'EttCableGlandType'): 'ett',
    ('ett', 'EttClimaticOption'): 'ett',
    ('ett', 'EttControlOptionsCombination'): 'ett',
    ('ett', 'EttControlSignal'): 'ett',
    ('ett', 'EttControlUnitDisplayType'): 'ett',
    ('ett', 'EttControlUnitHeater'): 'ett',
    ('ett', 'EttControlUnitType'): 'ett',
    ('ett', 'EttDocument'): 'ett',
    ('ett', 'EttElectricOptionsCombination'): 'ett',
    ('ett', 'EttFeedbackSignal'): 'ett',
    ('ett', 'EttMediumMaxTempOption'): 'ett',
    ('ett', 'EttOpenTime'): 'ett',
    ('ett', 'EttOtherOptionsCombination'): 'ett',
    ('ett', 'EttSeismicOption'): 'ett',
    ('ett', 'EttStatusSignal'): 'ett',
    ('ett', 'MtrType'): 'ett',
    ('ett', 'PnType'): 'ett',
    # --- Пневмоприводы ---
    ('pneumatic_actuators', 'BodyThrustTorqueTable'): 'pneumatic_actuators',
    ('pneumatic_actuators', 'PneumaticActuatorBody'): 'pneumatic_actuators',
    ('pneumatic_actuators', 'PneumaticActuatorBodyTable'): 'pneumatic_actuators',
    ('pneumatic_actuators', 'PneumaticActuatorConstructionVariety'): 'pneumatic_actuators',
    ('pneumatic_actuators', 'PneumaticActuatorModelLine'): 'pneumatic_actuators',
    ('pneumatic_actuators', 'PneumaticActuatorModelLineItem'): 'pneumatic_actuators',
    ('pneumatic_actuators', 'PneumaticActuatorSelected'): 'pneumatic_actuators',
    ('pneumatic_actuators', 'PneumaticActuatorSpringsQty'): 'pneumatic_actuators',
    ('pneumatic_actuators', 'PneumaticActuatorTechDataTable'): 'pneumatic_actuators',
    ('pneumatic_actuators', 'PneumaticActuatorTechDataTableDrawingItem'): 'pneumatic_actuators',
    ('pneumatic_actuators', 'PneumaticActuatorVariety'): 'pneumatic_actuators',
    # --- Фитинги ---
    ('pneumatic_fittings', 'FittingFixationMethod'): 'fittings',
    ('pneumatic_fittings', 'FittingShape'): 'fittings',
    ('pneumatic_fittings', 'PneumaticFitting'): 'fittings',
    ('pneumatic_fittings', 'PneumaticFittingModelLine'): 'fittings',
    ('pneumatic_fittings', 'PneumaticFittingVariety'): 'fittings',
    # --- Фильтры-регуляторы ---
    ('filter_regulator', 'DrainVariety'): 'filter_regulators',
    ('filter_regulator', 'FilterRegulator'): 'filter_regulators',
    ('filter_regulator', 'FilterRegulatorBody'): 'filter_regulators',
    ('filter_regulator', 'FilterRegulatorModelLine'): 'filter_regulators',
    ('filter_regulator', 'FilterRegulatorVariety'): 'filter_regulators',
    # --- Соленоидные клапаны ---
    ('solenoid_valves', 'DirectionValve'): 'solenoid_valves',
    ('solenoid_valves', 'DirectionValveBody'): 'solenoid_valves',
    ('solenoid_valves', 'DirectionalValveModelLine'): 'solenoid_valves',
    ('solenoid_valves', 'ManualOverride'): 'solenoid_valves',
    ('solenoid_valves', 'ValveActuationVariety'): 'solenoid_valves',
    ('solenoid_valves', 'ValveDesign'): 'solenoid_valves',
    ('solenoid_valves', 'ValveFunction'): 'solenoid_valves',
    ('solenoid_valves', 'ValveOperationVariety'): 'solenoid_valves',
    ('solenoid_valves', 'ValvePilotVariety'): 'solenoid_valves',
    # --- Редукторы ---
    ('gearbox', 'GearBox'): 'gearboxes',
    ('gearbox', 'GearBoxBody'): 'gearboxes',
    ('gearbox', 'GearBoxInterlock'): 'gearboxes',
    ('gearbox', 'GearBoxModelLine'): 'gearboxes',
    ('gearbox', 'GearboxVariety'): 'gearboxes',
    ('gearbox', 'OverrideMechanism'): 'gearboxes',
    ('gearbox', 'TransmissionVariety'): 'gearboxes',
    # --- Кабельные вводы ---
    ('cable_glands', 'CableGlandBody'): 'cable_glands',
    ('cable_glands', 'CableGlandBodyMaterial'): 'cable_glands',
    ('cable_glands', 'CableGlandItemType'): 'cable_glands',
    ('cable_glands', 'CableGlandModelLine'): 'cable_glands',
    # --- БКВ ---
    ('pa_controls', 'LimitSwitchBox'): 'lsb',
    ('pa_controls', 'LimitSwitchBody'): 'lsb',
    ('pa_controls', 'LimitSwitchModelLine'): 'lsb',
    ('pa_controls', 'LimitSwitchSensorVariety'): 'lsb',
    ('pa_controls', 'PointsOption'): 'lsb',
    ('pa_controls', 'ContactForm'): 'lsb',
    ('pa_controls', 'ContactState'): 'lsb',
    ('pa_controls', 'VisualIndicatorType'): 'lsb',
    ('pa_controls', 'SignalType'): 'lsb',
    ('pa_controls', 'SensorComponent'): 'lsb',
    ('pa_controls', 'PaControlMountingStandard'): 'lsb',
    # --- Позиционеры ---
    ('pa_controls', 'PosiModelLine'): 'positioners',
    ('pa_controls', 'PosiModelLineItem'): 'positioners',
    ('pa_controls', 'PosiBodyConnections'): 'positioners',
    ('pa_controls', 'LeverOption'): 'positioners',
    ('pa_controls', 'ActingType'): 'positioners',
    ('pa_controls', 'SmartCapabilityOption'): 'positioners',
    ('pa_controls', 'SmartCapabilitySet'): 'positioners',
    # --- Сигналы и профили ---
    ('params', 'ControlUnitSignalProfile'): 'signals',
    ('params', 'SignalRole'): 'signals',
    ('params', 'InputSignalSpec'): 'signals',
    # --- Взрывозащита ---
    ('params', 'ExdOption'): 'ex',
    ('params', 'HazardousGroup'): 'ex',
    ('params', 'TemperatureClass'): 'ex',
    ('params', 'ExplosionProtectionType'): 'ex',
    ('params', 'ExplosionProtectionLevel'): 'ex',
    ('params', 'ExplosionProtectionMethod'): 'ex',
    # --- Резьбы и присоединения ---
    ('params', 'ThreadTypes'): 'threads',
    ('params', 'ThreadSize'): 'threads',
    ('params', 'ThreadSizeSet'): 'threads',
    ('params', 'ThreadSizeSetItem'): 'threads',
    ('params', 'ThreadInnerOuter'): 'threads',
    ('params', 'PneumaticConnection'): 'threads',
    ('params', 'MountingPlateTypes'): 'threads',
    ('params', 'StemShapes'): 'threads',
    ('params', 'StemSize'): 'threads',
    # --- Климатика и степень защиты ---
    ('params', 'IpOption'): 'climate',
    ('params', 'ClimaticConditions'): 'climate',
    ('params', 'ClimaticZoneCategory'): 'climate',
    ('params', 'ClimaticPlacementCategory'): 'climate',
    ('params', 'EnvTempParameters'): 'climate',
    # --- Управление и индикация ---
    ('params', 'ControlUnitTypeOption'): 'control',
    ('params', 'ControlUnitLocationOption'): 'control',
    ('params', 'ControlUnitInstalledOption'): 'control',
    ('params', 'SwitchesParameters'): 'control',
    ('params', 'DigitalProtocolsSupportOption'): 'control',
    ('params', 'SafetyPositionOption'): 'control',
    ('params', 'OperatingModeOption'): 'control',
    ('params', 'HandWheelInstalledOption'): 'control',
    ('params', 'MechanicalIndicatorInstalledOption'): 'control',
    ('params', 'BlinkerOption'): 'control',
    ('params', 'PowerSupplies'): 'control',
    ('params', 'ActuatorHeaterSupply'): 'control',
    ('params', 'TurnCounterOption'): 'control',
    ('params', 'ActuatorGearboxOutputType'): 'control',
    ('params', 'ActuatorGearBoxCombinationTypes'): 'control',
    ('params', 'LockingMechanism'): 'control',
    # --- Покрытия и цвета ---
    ('params', 'BodyCoatingOption'): 'coatings',
    ('params', 'CoatingVariety'): 'coatings',
    ('params', 'BodyColor'): 'coatings',
    # --- Сертификаты ---
    ('cert_doc', 'CertData'): 'certs',
    ('cert_doc', 'CertVariety'): 'certs',
    ('params', 'CertData'): 'certs',
    ('params', 'CertVariety'): 'certs',
    # --- Справочники (прочие) ---
    ('params', 'MeasureUnits'): 'dicts',
    ('params', 'DnVariety'): 'dicts',
    ('params', 'PnVariety'): 'dicts',
    ('params', 'ValveTypes'): 'dicts',
    ('params', 'ValveFunctionVariety'): 'dicts',
    ('params', 'ValveActuationVariety'): 'dicts',
    ('params', 'SealingClass'): 'dicts',
    ('params', 'OptionVariety'): 'dicts',
    ('params', 'WarrantyTimePeriodVariety'): 'dicts',
    ('params', 'PneumaticAirSupplyPressure'): 'dicts',
    ('features', 'FeatureSet'): 'dicts',
    ('features', 'FeatureTemplate'): 'dicts',
    ('features', 'FeatureVariety'): 'dicts',
    # --- Материалы ---
    ('materials', 'MaterialChemicalResistance'): 'materials',
    ('materials', 'MaterialCode'): 'materials',
    ('materials', 'MaterialGeneral'): 'materials',
    ('materials', 'MaterialGeneralMoreDetailed'): 'materials',
    ('materials', 'MaterialSpecified'): 'materials',
    ('materials', 'MaterialStandard'): 'materials',
    ('materials', 'WorkingMedium'): 'materials',
    # --- Медиабиблиотека ---
    ('media_library', 'ImageGallerySet'): 'media',
    ('media_library', 'MediaCategory'): 'media',
    ('media_library', 'MediaLibraryItem'): 'media',
    # --- Бренды и производители ---
    ('producers', 'Brands'): 'producers',
    ('producers', 'Producer'): 'producers',
    # --- Цены и валюты ---
    ('price', 'Currency'): 'prices',
    ('price', 'EAPriceConstructor'): 'prices',
    ('price', 'EAPriceDocument'): 'prices',
    ('price', 'ExchangeRate'): 'prices',
    ('price', 'PriceDocument'): 'prices',
    ('price', 'PriceHistory'): 'prices',
    ('price', 'PriceVariety'): 'prices',
    # --- Конфигуратор и мастера ---
    ('configurator', 'DerivationRule'): 'configurator',
    ('configurator', 'EquipmentTypeParameter'): 'configurator',
    ('configurator', 'FittingPattern'): 'configurator',
    ('configurator', 'FittingPatternItem'): 'configurator',
    ('configurator', 'ModelFieldSnapshot'): 'configurator',
    ('configurator', 'ParameterBinding'): 'configurator',
    ('configurator', 'ParameterCatalog'): 'configurator',
    ('configurator', 'ParameterRule'): 'configurator',
    ('core', 'EquipmentType'): 'configurator',
    ('core', 'SelectionWizard'): 'configurator',
    ('assemblies', 'AssemblyRequirements'): 'configurator',
    ('assemblies', 'ComponentRequirement'): 'configurator',
    # --- Номенклатура ---
    ('sku', 'MBOM'): 'sku',
    ('sku', 'MBOMItem'): 'sku',
    ('sku', 'SKU'): 'sku',
    # --- Заявки клиентов ---
    ('client_requests', 'ClientRequest'): 'requests',
    ('client_requests', 'ClientRequestComment'): 'requests',
    ('client_requests', 'ClientRequestItem'): 'requests',
    ('client_requests', 'ClientRequestStatus'): 'requests',
    ('client_requests', 'CommentType'): 'requests',
    ('client_requests', 'RequestChangeLog'): 'requests',
    ('client_requests', 'RequestItemComment'): 'requests',
    ('client_requests', 'RequestItemType'): 'requests',
    ('client_requests', 'RequestNumberCounter'): 'requests',
    ('client_requests', 'RequestSnapshot'): 'requests',
    ('cart', 'Cart'): 'requests',
    ('cart', 'CartItem'): 'requests',
    # --- Клиенты и доступ ---
    ('clients', 'Company'): 'customers',
    ('clients', 'CompanyPerson'): 'customers',
    ('project_customers', 'AllowedApp'): 'customers',
    ('project_customers', 'CustomerApiKey'): 'customers',
    ('project_customers', 'CustomerAppAccess'): 'customers',
    ('project_customers', 'CustomerEmail'): 'customers',
    ('project_customers', 'CustomerSettings'): 'customers',
    ('project_customers', 'FavoriteBrand'): 'customers',
    ('project_customers', 'LegalEntity'): 'customers',
    ('project_customers', 'ProjectCustomer'): 'customers',
    ('project_customers', 'ProjectCustomerUser'): 'customers',
    ('project_customers', 'Role'): 'customers',
    ('project_customers', 'SiteSection'): 'customers',
    ('project_customers', 'UserParameter'): 'customers',
    ('project_customers', 'UserSettings'): 'customers',
    # --- AI-ассистент ---
    ('ai_assistant', 'AIClientProvider'): 'ai',
    ('ai_assistant', 'AIConversation'): 'ai',
    ('ai_assistant', 'AIMessage'): 'ai',
    ('ai_assistant', 'AIPromptTemplate'): 'ai',
    ('ai_assistant', 'AIProvider'): 'ai',
    ('ai_assistant', 'AIQuerySample'): 'ai',
    ('ai_assistant', 'AITokenUsage'): 'ai',
    ('ai_assistant', 'CompositionGroup'): 'ai',
    ('ai_assistant', 'JSONSchema'): 'ai',
    ('ai_assistant', 'PipelineSkill'): 'ai',
    ('ai_assistant', 'SelectionNode'): 'ai',
    ('ai_assistant', 'SkillOverride'): 'ai',
    # --- Система ---
    ('auth', 'Group'): 'system',
    ('auth', 'User'): 'system',
    ('admin_interface', 'Theme'): 'system',
}


class GroupedAdminSite(AdminSite):
    """AdminSite, чья главная страница группирует модели по разделам ADMIN_BLOCKS."""

    index_template = 'admin/grouped_index.html'

    def get_app_list(self, request, app_label=None):
        """Группирует модели по разделам; незамапленные — в «Новые модели».

        Права и URL каждой модели берутся готовыми из super().get_app_list(),
        поэтому фильтрация по правам пользователя сохраняется автоматически.
        """
        if app_label is not None:
            # Страницы отдельных приложений оставляем как есть.
            return super().get_app_list(request, app_label)

        app_list = super().get_app_list(request)

        blocks = {
            bid: {
                'name': title,
                'app_label': bid,
                'app_url': None,
                'has_module_perms': True,
                'models': [],
                'description': description,
            }
            for bid, title, description in ADMIN_BLOCKS
        }
        blocks[NEW_MODELS_BLOCK] = {
            'name': NEW_MODELS_TITLE,
            'app_label': NEW_MODELS_BLOCK,
            'app_url': None,
            'has_module_perms': True,
            'models': [],
            'description': NEW_MODELS_DESC,
        }

        for app in app_list:
            for model in app['models']:
                # Сохраняем исходное приложение модели — используется в шаблоне
                # для уникальных id (в одном блоке могут быть одноимённые модели
                # из разных приложений, например cert_doc.CertData и params.CertData).
                model['origin_app'] = app['app_label']
                key = (app['app_label'], model['object_name'])
                blocks[ADMIN_MODEL_BLOCK.get(key, NEW_MODELS_BLOCK)]['models'].append(model)

        order = [bid for bid, _, _ in ADMIN_BLOCKS] + [NEW_MODELS_BLOCK]
        return [blocks[bid] for bid in order if blocks[bid]['models']]


# Реестр ModelAdmin'ов переносится из admin.site целиком: к моменту импорта
# этого модуля (загрузка URLConf) все admin.py приложений уже отработали.
grouped_admin_site = GroupedAdminSite(name='admin')
grouped_admin_site._registry.update(admin.site._registry)

# ModelAdmin.admin_site должен указывать на работающий сайт: иначе кастомные
# страницы моделей (admin_view/each_context) используют admin.site и видят
# старый плоский список приложений вместо сгруппированного.
for _model_admin in grouped_admin_site._registry.values():
    _model_admin.admin_site = grouped_admin_site

# Предупреждение о «мёртвых» ключах словаря (модель удалена/переименована):
# такие записи молча игнорируются и засоряют конфигурацию.
_registry_keys = {
    (model._meta.app_label, model._meta.object_name)
    for model in grouped_admin_site._registry
}
_stale_keys = sorted(key for key in ADMIN_MODEL_BLOCK if key not in _registry_keys)
if _stale_keys:
    logging.getLogger(__name__).warning(
        'djangoProject1.admin_site: ключи ADMIN_MODEL_BLOCK отсутствуют в реестре админки: %s',
        _stale_keys,
    )
