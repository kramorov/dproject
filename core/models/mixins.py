# core/models/mixins.py
from django.db import models
from django.utils import timezone
from django.utils.formats import date_format
from django.contrib import admin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from typing import Dict , List , Optional , Any
from ..constants import DataFormat , DisplayView
from typing import TypeVar , Any , Dict , Callable , Optional
import logging
from django.contrib import messages
logger = logging.getLogger(__name__)
import copy

class TemplateMixin:
    """
    Миксин для генерации названий и описаний из шаблонов.
    Включает в себя методы получения значений по путям (_get_value).
    """

    # === МЕТОДЫ ПОЛУЧЕНИЯ ЗНАЧЕНИЙ (поля, связи, JSON) ===
    def _get_value(self, field_path: str) -> str:
        """Универсальное получение значения по пути (поля, связи, JSON)."""
        # print(f'TemplateMixin: _get_value field_path:{field_path}')
        try:
            return self._get_field_value(field_path)
        except Exception as e:
            logger.error(f"Ошибка получения {field_path}: {e}")
            return ""

    def _get_field_value(self, field_path: str) -> str:
        """Реализация получения значения (без вызова методов)."""
        # print(f"\n{'=' * 60}")
        # print(f"[GET_FIELD_VALUE] НАЧАЛО: field_path='{field_path}'")
        # print(f"{'=' * 60}")

        current_obj = self
        parts = field_path.split('__')
        # print(f"[GET_FIELD_VALUE] Разбито на части: {parts}")

        for i, part in enumerate(parts):
            # print(f"\n--- Шаг {i} ---")
            # print(f"  Обработка part='{part}'")
            # print(f"  Текущий объект: {current_obj}")
            # print(f"  Тип current_obj: {type(current_obj).__name__}")

            if '.' in part:
                json_field, json_key = part.split('.', 1)
                # print(f"  JSON формат: json_field='{json_field}', json_key='{json_key}'")

                if hasattr(current_obj, json_field):
                    current_obj = getattr(current_obj, json_field)
                    # print(f"  Получен current_obj: {current_obj}")
                    # print(f"  Тип после getattr: {type(current_obj).__name__}")

                    if isinstance(current_obj, dict):
                        current_obj = current_obj.get(json_key, '')
                        # print(f"  Извлечено из dict: '{current_obj}'")
                    else:
                        print(f"  ОШИБКА: Объект не dict (тип: {type(current_obj).__name__})")
                        return ""
                else:
                    print(f"  ОШИБКА: Нет атрибута '{json_field}' у {type(current_obj).__name__}")
                    return ""
            else:
                # print(f"  Обычное поле: '{part}'")

                if hasattr(current_obj, part):
                    current_obj = getattr(current_obj, part)
                    # print(f"  Получено значение: '{current_obj}'")
                    # print(f"  Тип значения: {type(current_obj).__name__}")

                    if current_obj is None:
                        print(f"  Значение None, возвращаем пустую строку")
                        return ""
                else:
                    print(f"  ОШИБКА: Нет атрибута '{part}' у {type(current_obj).__name__}")
                    print(
                        f"  Доступные атрибуты: {[attr for attr in dir(current_obj) if not attr.startswith('_')][:10]}...")
                    return ""

        result = str(current_obj) if current_obj is not None else ""
        # print(f"\n{'=' * 60}")
        # print(f"[GET_FIELD_VALUE] для шаблона РЕЗУЛЬТАТ: '{result}'")
        # print(f"  Исходный тип: {type(current_obj).__name__}")
        # print(f"{'=' * 60}\n")
        return result

    # === МЕТОДЫ ДЛЯ ПЕРЕОПРЕДЕЛЕНИЯ В МОДЕЛИ ===
    def _get_name_template_source(self):
        """Переопределить в модели: вернуть шаблон названия или None."""
        return None

    def _get_description_template_source(self):
        """Переопределить в модели: вернуть шаблон описания или None."""
        return None

    def _get_title_template_source(self):
        """Переопределить в модели: вернуть шаблон заголовка или None."""
        return None

    def _get_equipment_type_template(self, field: str) -> str:
        """Получить шаблон из EquipmentType (админная настройка).
        Ищет через model_line.equipment_type или прямой equipment_type."""
        try:
            et = None
            ml = getattr(self, 'model_line', None)
            if ml and hasattr(ml, 'equipment_type_id') and ml.equipment_type_id:
                et = ml.equipment_type
            if et is None and hasattr(self, 'equipment_type_id') and self.equipment_type_id:
                et = self.equipment_type
            if et is not None:
                return getattr(et, field, None) or ''
        except Exception:
            pass
        return ''

    # === ДЕФОЛТНЫЕ ШАБЛОНЫ ===
    def _get_default_name_template(self) -> str:
        return "{model_code}"

    def _get_default_description_template(self) -> str:
        return "{model_code}"

    def _get_default_title_template(self) -> str:
        """Дефолтный шаблон заголовка."""
        return "{model_code}"


    # === СЛОВАРЬ ДЛЯ ПОДСТАНОВКИ ===
    def _get_data_dict(self) -> Dict[str, str]:
        """Переопределить в модели: вернуть словарь {плейсхолдер: значение/путь}."""
        return {
            '{model_code}': 'code',
        }

    def _get_model_meta_name(self) -> str:
        """
        Возвращает читаемое имя модели для сообщений об ошибках.
        Перенесено из TemplateFillerMixin при консолидации дублирующих миксинов (2026-06-05).
        """
        if hasattr(self, '_meta') and hasattr(self._meta, 'verbose_name'):
            return self._meta.verbose_name
        return self.__class__.__name__

    # === ИТОГОВЫЕ ШАБЛОНЫ ===
    @property
    def get_extra_params(self, separator: str = "; ", name_value_separator: str = ": ") -> str:
        """
        Формирует строку дополнительных параметров из JSON поля extra_params.

        Args:
            separator: Разделитель между параметрами (по умолчанию "; ")
            name_value_separator: Разделитель между именем и значением (по умолчанию ": ")

        Returns:
            Строка вида "name1: value1; name2: value2; ..."
        """
        if not self.extra_params:
            return ""

        # Если extra_params строка, парсим её
        if isinstance(self.extra_params, str):
            try:
                import json
                params_dict = json.loads(self.extra_params)
            except (json.JSONDecodeError, TypeError):
                return ""
        else:
            params_dict = self.extra_params

        if not isinstance(params_dict, dict):
            return ""

        # Формируем строку параметров
        result_parts = []
        for key, value in params_dict.items():
            if not value:
                continue

            if isinstance(value, dict):
                name = value.get('name', key)
                val = value.get('value', '')
                if val:
                    result_parts.append(f"{name}{name_value_separator}{val}")
        return separator.join(result_parts)

    @property
    def name_template(self) -> str:
        return self._get_name_template_source() or self._get_default_name_template()

    @property
    def title_template(self) -> str:
        """Итоговый шаблон заголовка: source или default."""
        et = self._get_equipment_type_template('title_template')
        if et:
            return et
        return self._get_title_template_source() or self._get_default_title_template()

    @property
    def description_template(self) -> str:
        return self._get_description_template_source() or self._get_default_description_template()



    # === ЗАПОЛНЕНИЕ ШАБЛОНА ===
    def _fill_template(self, template: str, data_dict: Dict[str, str] = None, hide_code: bool = False) -> str:
        import re

        if not template:
            return ""

        # Находим все плейсхолдеры в шаблоне
        placeholders_in_template = set(re.findall(r'\{([^{}]+)\}', template))

        if not placeholders_in_template:
            # Нет плейсхолдеров - возвращаем шаблон как есть
            return template.strip()

        # Получаем маппинг только если он нужен
        if data_dict is None:
            full_data_dict = self._get_data_dict()
        else:
            full_data_dict = data_dict

        # Создаем словарь только с нужными плейсхолдерами
        result = template

        for placeholder in placeholders_in_template:
            # Формируем ключ с фигурными скобками для поиска в словаре
            dict_key = f'{{{placeholder}}}'

            if dict_key in full_data_dict:
                # Получаем путь к значению
                path = full_data_dict[dict_key]
                # Получаем значение по пути
                value = self._get_value(path)
                # Заменяем плейсхолдер
                result = result.replace(dict_key, str(value) if value is not None else "")
            else:
                # Если плейсхолдер не найден в словаре, заменяем на пустую строку
                # или можно залогировать предупреждение
                print(f"[WARNING] Плейсхолдер {dict_key} не найден в data_dict")
                result = result.replace(dict_key, "")

        # Очищаем от оставшихся незамененных плейсхолдеров (на всякий случай)
        result = re.sub(r'\{[^{}]+\}', '', result)
        # Убираем лишние пробелы
        result = re.sub(r'\s+', ' ', result).strip()

        return result

    # === ГЕНЕРАЦИЯ СТРОК ===
    def generate_name(self) -> str:
        return self._fill_template(self.name_template)

    def generate_description(self) -> str:
        return self._fill_template(self.description_template)

    def get_display_name(self) -> str:
        return self.generate_name()

    def get_display_description(self) -> str:
        return self.generate_description()

    def generate_title(self) -> str:
        """Сгенерировать заголовок из шаблона title_template."""
        # print(f'Mixin template generate_title={self._fill_template(self.title_template)}, template={self.title_template}')
        return self._fill_template(self.title_template)

    # === ОБНОВЛЕНИЕ ПОЛЕЙ МОДЕЛИ ===
    def update_name(self, save: bool = False) -> bool:
        generated = self.generate_name()
        if generated and getattr(self, 'name', "") != generated:
            self.name = generated
            if save:
                self.save(skip_auto_generate=True)
            return True
        return False

    def update_description(self, save: bool = False) -> bool:
        generated = self.generate_description()
        if generated and getattr(self, 'description', "") != generated:
            self.description = generated
            if save:
                self.save(skip_auto_generate=True)
            return True
        return False

    def update_from_templates(self, save: bool = False) -> bool:
        name_updated = self.update_name(save=False)
        desc_updated = self.update_description(save=False)
        if save and (name_updated or desc_updated):
            self.save(skip_auto_generate=True)
        return name_updated or desc_updated

    # === СОХРАНЕНИЕ ===
    def save(self, *args, **kwargs):
        skip_auto_generate = kwargs.pop('skip_auto_generate', False)
        if not skip_auto_generate:
            self.update_name(save=False)
            self.update_description(save=False)
        super().save(*args, **kwargs)


    # === ГЕНЕРАЦИЯ ИЗ ШАБЛОНОВ MODEL_LINE (консолидировано из TemplateGeneratorMixin 2026-09-01) ===

    def generated_model_name_description(self, name_or_description: str, hide_code: bool = False) -> str:
        """Сгенерировать название или описание по шаблону из model_line."""
        model_name = self._get_model_meta_name()
        if not getattr(self, 'model_line', None):
            return self.name or ""
        if name_or_description == 'name':
            template = self.model_line.name_template
            if not template or not template.strip():
                template = self._get_default_name_template()
                if not template or not template.strip():
                    logger.error(f'Ошибка при формировании названия в {model_name} - нет шаблона')
                    return self.name or ""
        else:
            template = self.model_line.description_template
            if not template or not template.strip():
                template = self._get_default_description_template()
                if not template or not template.strip():
                    logger.error(f'Ошибка при формировании описания в {model_name} - нет шаблона')
                    return self.description or ""
        placeholder_to_attr = self._get_data_dict()
        return self._fill_template(template, placeholder_to_attr, hide_code)

    def _process_m2m_field(self, related_manager, item_template: str, separator: str = ", ",
                           last_separator: str = None) -> str:
        """Универсальная обработка M2M полей в шаблонах."""
        items = related_manager.all()
        if not items:
            return ""
        result_items = []
        for item in items:
            if hasattr(item, '_fill_template'):
                result_items.append(item._fill_template(item_template))
            else:
                filled = item_template
                for attr in ['name', 'code', 'full_code', 'description']:
                    if f'{{{attr}}}' in filled:
                        value = getattr(item, attr, '')
                        filled = filled.replace(f'{{{attr}}}', str(value) if value else '')
                result_items.append(filled)
        if len(result_items) == 1:
            return result_items[0]
        if len(result_items) == 2 and last_separator:
            return f"{result_items[0]} {last_separator} {result_items[1]}"
        if len(result_items) > 2 and last_separator:
            return f"{', '.join(result_items[:-1])} {last_separator} {result_items[-1]}"
        return separator.join(result_items)

    def update_name_from_template(self):
        """Обновить название из шаблона model_line."""
        if getattr(self, 'model_line', None) and self.model_line.name_template:
            generated_name = self.generated_model_name_description('name')
            if generated_name:
                self.name = generated_name
                return True
        return False

    def update_description_from_template(self):
        """Обновить описание из шаблона model_line."""
        if getattr(self, 'model_line', None) and self.model_line.description_template:
            generated_description = self.generated_model_name_description('description')
            if generated_description:
                self.description = generated_description
                return True
        return False

    def update_name_and_description_from_templates(self):
        """Обновить название и описание из шаблонов model_line."""
        name_updated = self.update_name_from_template()
        description_updated = self.update_description_from_template()
        return name_updated or description_updated


# ══════════════════════════════════════════════════════════════════════════════
# TemplateFillerMixin — закомментирован 2026-06-05.
# Причина: _fill_template(), _get_value(), _get_data_dict(), _get_model_meta_name()
# дублировали те же методы из TemplateMixin. При наличии TemplateMixin в MRO
# TemplateFillerMixin был недостижим. Единственный прямой пользователь —
# LimitSwitchSensorVariety — не использовал ни один метод.
# Код закомментирован, не удалён — удалить после следующего релиза.
# ══════════════════════════════════════════════════════════════════════════════
# class TemplateFillerMixin:
#     """
#     Миксин для заполнения шаблонов значениями из полей модели.
#     Не требует model_line и других зависимостей.
#     """

#     def _get_data_dict(self) -> Dict[str, str]:
#         """
#         Должен быть переопределен в модели.
#         Возвращает словарь {плейсхолдер: путь_к_атрибуту}
#         """
#         return {}
#
#     def _get_value(self, attr_path: str) -> str:
#         """
#         Получает значение по вложенному пути.
#         Поддерживает:
#         - Обычные поля: 'code'
#         - Связи через __: 'brand__name'
#         - JSON поля через .: 'extra_params.material'
#         """
#         try:
#             current = self
#             # Заменяем . на __ для единообразия
#             path = attr_path.replace('.', '__')
#             for part in path.split('__'):
#                 if hasattr(current, part):
#                     current = getattr(current, part)
#                     if current is None:
#                         return ""
#                 elif isinstance(current, dict) and part in current:
#                     current = current.get(part, "")
#                 else:
#                     return ""
#             return str(current) if current is not None else ""
#         except Exception:
#             return ""
#
#     def _get_model_meta_name(self) -> str:
#         """Возвращает имя модели для логов"""
#         return self.__class__.__name__
#
#     def _fill_template(self, template_str: str, placeholder_to_attr: Dict[str, str] = None, hide_code: bool = False) -> str:
#         """
#         Заполняет шаблон значениями из словаря.
#
#         Args:
#             template_str: шаблон с плейсхолдерами {placeholder}
#             placeholder_to_attr: словарь соответствий (если None, то используется self._get_data_dict())
#             hide_code: игнорируется в этом миксине, оставлен для совместимости
#
#         Returns:
#             Заполненная строка
#         """
#         if not template_str:
#             return ""
#
#         if placeholder_to_attr is None:
#             placeholder_to_attr = self._get_data_dict()
#
#         result = template_str
#         for placeholder, attr_path in placeholder_to_attr.items():
#             value = self._get_value(attr_path)
#             result = result.replace(placeholder, str(value) if value is not None else "")
#
#         return result


#
# class ValueGetterMixin:
#     """
#     Миксин для универсального получения значений из полей модели:
#     - Обычные поля
#     - Связанные поля через __
#     - JSON поля через .
#     - Комбинации
#     """
#
#     def _get_value(self, field_path: str) -> str:
#         """
#         Универсальное получение значения:
#         - Обычные поля: 'code'
#         - Связи через __: 'body__material'
#         - JSON поля через .: 'extra_params.ip_rating'
#         - Комбинация: 'body__extra_params.cable_glands_holes'
#         """
#         try:
#             current_obj = self
#
#             # Разбиваем на части
#             parts = field_path.split('__')
#
#             for part in parts:
#                 # Проверяем, есть ли доступ к JSON через точку
#                 if '.' in part:
#                     json_field, json_key = part.split('.', 1)
#                     if hasattr(current_obj, json_field):
#                         current_obj = getattr(current_obj, json_field)
#                         if isinstance(current_obj, dict):
#                             current_obj = current_obj.get(json_key, '')
#                         else:
#                             return ""
#                     else:
#                         return ""
#                 else:
#                     if hasattr(current_obj, part):
#                         current_obj = getattr(current_obj, part)
#                         if current_obj is None:
#                             return ""
#                     else:
#                         return ""
#
#             return str(current_obj) if current_obj else ""
#         except Exception as e:
#             logger.error(f"Ошибка получения {field_path}: {e}")
#             return ""
#
#
# class TemplateGeneratorMixin(ValueGetterMixin):
#     """
#     Миксин для генерации названий и описаний из шаблонов
#     """
#     # Объявляем атрибуты, которые будут доступны в моделях, использующих миксин
#     name: str
#     code: Optional[str]
#     description: str
#     model_line: Optional[Any]  # Any вместо конкретного типа, чтобы избежать циклических импортов
#
#     def _get_default_name_template(self) -> str:
#         """
#         Получить шаблон описания по умолчанию. Должен быть переопределен в каждой модели.
#         """
#         return "{model_code} "
#
#     def _get_default_description_template(self) -> str:
#         """
#         Получить шаблон описания по умолчанию. Должен быть переопределен в каждой модели.
#         """
#         return "{model_code} "
#     def _get_data_dict(self):
#         """
#         Получить словарь соответствий плейсхолдеров и атрибутов для замены.
#         Должен быть переопределен в каждой модели.
#         """
#         print(f'_get_data_dict from TemplateGeneratorMixin')
#         return {
#             '{model_code}': 'code',
#
#         }
#
#     def _fill_template(self , template_str: str , placeholder_to_attr: Dict[str , str] ,
#                        hide_code: bool = False) -> str :
#         """
#         Заполняет шаблон значениями из словаря
#
#         Args:
#             template_str: шаблон с плейсхолдерами {placeholder}
#             placeholder_to_attr: словарь соответствия плейсхолдеров и путей к атрибутам
#             hide_code: скрыть ли {model_code}
#
#         Returns:
#             Заполненная строка
#         """
#         if not template_str :
#             return ""
#
#         result = template_str
#         for placeholder , attr_path in placeholder_to_attr.items() :
#             value = self._get_value(attr_path)
#
#             # Если hide_code=True и это плейсхолдер для model_code - скрываем
#             if hide_code and placeholder == '{model_code}' :
#                 value = ""
#
#             result = result.replace(placeholder , str(value) if value is not None else "")
#
#         return result
#
#     def generated_model_name_description(self , name_or_description: str , hide_code: bool = False) -> str :
#         """
#         Сгенерировать название или описание по шаблону из model_line
#
#         Args:
#             name_or_description: 'name' или 'description' - что генерировать
#             hide_code: скрыть model_code при генерации
#         """
#         model_name = self._get_model_meta_name()
#
#         if not self.model_line :
#             return self.name or ""
#
#         # Выбираем шаблон
#         if name_or_description == 'name' :
#             template = self.model_line.name_template
#             if not template or not template.strip() :
#                 template = self._get_default_name_template()
#                 if not template or not template.strip() :
#                     logger.error(
#                         f'Ошибка при формировании названия в {model_name} - '
#                         f'нет шаблона названия (ни в model_line, ни дефолтного)'
#                     )
#                     return self.name or ""
#         else :
#             template = self.model_line.description_template
#             if not template or not template.strip() :
#                 template = self._get_default_description_template()
#                 if not template or not template.strip() :
#                     logger.error(
#                         f'Ошибка при формировании описания в {model_name} - '
#                         f'нет шаблона описания (ни в model_line, ни дефолтного)'
#                     )
#                     return self.description or ""
#
#         # Получаем словарь соответствий
#         placeholder_to_attr = self._get_data_dict()
#
#         # Заполняем шаблон
#         result = self._fill_template(template , placeholder_to_attr , hide_code)
#
#         return result
#
#     def update_name_from_template(self):
#         """Обновить название из шаблона"""
#         print(f'update_name_from_template from TemplateGeneratorMixin')
#         if self.model_line and self.model_line.name_template:
#             generated_name = self.generated_model_name_description('name')
#             if generated_name:
#                 self.name = generated_name
#                 return True
#         return False
#
#     def update_description_from_template(self):
#         """Обновить описание из шаблона"""
#         if self.model_line and self.model_line.description_template:
#             generated_description = self.generated_model_name_description('description')
#             if generated_description:
#                 self.description = generated_description
#                 return True
#         return False
#
#     def update_name_and_description_from_templates(self):
#         """Обновить название и описание из шаблонов"""
#         name_updated = self.update_name_from_template()
#         description_updated = self.update_description_from_template()
#         return name_updated or description_updated
#
#     def save(self, *args, **kwargs):
#         """При сохранении обновляем название и описание из шаблонов, если не указано в параметрах skip_auto_generate=True"""
#         skip_auto_generate = kwargs.pop('skip_auto_generate', False)
#         # print(f'save from TemplateGeneratorMixin. skip_auto_generate={skip_auto_generate}')
#         if not skip_auto_generate:
#             self.update_name_and_description_from_templates()
#         super().save(*args, **kwargs)
#
#     def _get_model_meta_name(self):
#         """Получить название модели из Meta"""
#         if hasattr(self, '_meta') and hasattr(self._meta, 'verbose_name'):
#             return self._meta.verbose_name
#         return self.__class__.__name__

class StructuredDataMixin :
    """
    Миксин для структурированных данных.
    Должен быть реализован в каждой модели.
    """
    # Константы для удобства
    COMPACT = DataFormat.COMPACT
    DISPLAY = DataFormat.DISPLAY
    FULL = DataFormat.FULL
    """Типы отображения
    LIST = 'list'
    CARD = 'card'
    DETAIL = 'detail'
    BADGE = 'badge'
    INLINE = 'inline'"""
    LIST = DisplayView.LIST
    CARD = DisplayView.CARD
    DETAIL = DisplayView.DETAIL
    BADGE = DisplayView.BADGE



    def save(self, *args, **kwargs):
        """При сохранении обновляем название и описание из шаблонов, если не указано в параметрах """
        # print(f"[DEBUG] save: name='{self._get_model_name()}'\")  # silenced 2026-06-04
        super().save(*args, **kwargs)

    def _get_model_meta_name(self):
        """Получить название модели из Meta"""
        if hasattr(self, '_meta') and hasattr(self._meta, 'verbose_name'):
            return self._meta.verbose_name
        return self.__class__.__name__
    # Новая версия, с JSON
    def _get_value(self , field_path: str) -> str :
        """
        Универсальное получение значения:
        - Обычные поля: 'code'
        - Связи через __: 'body__material'
        - JSON поля через .: 'extra_params.ip_rating'
        - Комбинация: 'body__extra_params.cable_glands_holes'
        """
        try :
            current_obj = self

            # Разбиваем на части
            parts = field_path.split('__')

            for part in parts :
                # Проверяем, есть ли доступ к JSON через точку
                if '.' in part :
                    json_field , json_key = part.split('.' , 1)
                    if hasattr(current_obj , json_field) :
                        current_obj = getattr(current_obj , json_field)
                        if isinstance(current_obj , dict) :
                            current_obj = current_obj.get(json_key , '')
                        else :
                            return ""
                    else :
                        return ""
                else :
                    if hasattr(current_obj , part) :
                        current_obj = getattr(current_obj , part)
                        if current_obj is None :
                            return ""
                    else :
                        return ""

            return str(current_obj) if current_obj else ""
        except Exception as e :
            print(f"Ошибка получения {field_path}: {e}")
            return ""

    def get_compact_data(self) -> Dict[str , Any] :
        """
        Минимальные данные для списков и таблиц.
        Должен быть переопределен в каждой модели.
        """
        obj_id = getattr(self , 'id' , None)  # Безопасное получение id
        # Безопасный доступ к метаданным модели
        model_name = self._get_model_name()
        app_label = self._get_app_label()

        return {
            'id' : obj_id,  # Используем безопасное значение
            'name' : getattr(self , 'name' , None) ,
            'code' : getattr(self , 'code' , None) ,
            'is_active' : getattr(self , 'is_active' , True) ,
            'model' : model_name ,
            'app' : app_label ,
        }

    def get_display_data(self , view_type: str = DETAIL) -> Dict[str , Any] :
        """
        Данные для отображения в UI.
        Должен быть переопределен в каждой модели.

        Args:
            view_type: тип отображения (LIST, CARD, DETAIL, BADGE)
        """
        raise NotImplementedError(
            f"Модель {self.__class__.__name__} должна реализовать get_display_data()"
        )

    def get_full_data(self , include: Optional[List[str]] = None) -> Dict[str , Any] :
        """
        Полные данные для форм и API.
        Должен быть переопределен в каждой модели.

        Args:
            include: что включать ['form', 'metadata', 'related', 'audit']
        """
        raise NotImplementedError(
            f"Модель {self.__class__.__name__} должна реализовать get_full_data()"
        )

    # Общие вспомогательные методы
    def _format_field(self , value , field_type: str = 'text' , **kwargs) -> Dict[str , Any] :
        """Форматирование поля с метаданными"""


        default_value = kwargs.get('default' , '—')

        if value is None or value == '' :
            formatted_value = default_value
            is_empty = True
        else :
            formatted_value = str(value)
            is_empty = False

        result = {
            'value' : value ,
            'formatted' : formatted_value ,
            'type' : field_type ,
            'is_empty' : is_empty ,
            'raw' : value ,
        }

        # Добавляем дополнительные параметры
        for key in ['label' , 'icon' , 'priority' , 'multiline' , 'required'] :
            if key in kwargs :
                result[key] = kwargs[key]

        return result

    def _format_date(self , date_obj , format_str: str = 'd.m.Y') -> Dict[str , Any] :
        """Форматирование даты"""
        if not date_obj :
            return self._format_field(None , 'date' , default='Не указана')

        return self._format_field(
            date_obj ,
            'date' ,
            formatted=date_format(date_obj , format_str) ,
            iso_format=date_obj.isoformat() if hasattr(date_obj , 'isoformat') else None
        )

    def _format_datetime(self , datetime_obj , format_str: str = 'd.m.Y H:i' , **kwargs) -> Dict[str , Any] :
        """
        Форматирование даты-времени
        """
        if not datetime_obj :
            default_text = kwargs.pop('default' , _('Не указано'))
            return self._format_field(None , 'datetime' , default=default_text , **kwargs)

        formatted = date_format(datetime_obj , format_str)
        return self._format_field(
            datetime_obj ,
            'datetime' ,
            formatted=formatted ,
            iso_format=datetime_obj.isoformat() if hasattr(datetime_obj , 'isoformat') else None ,
            **kwargs
        )

    def _format_foreign_key(self , obj , **kwargs) -> Dict[str , Any] :
        """
        Форматирование ForeignKey поля

        Args:
            obj: связанный объект
            **kwargs: дополнительные параметры:
                - label: подпись поля
                - icon: иконка
                - priority: приоритет
                - include_data: какие данные включать ('compact', 'display', 'full')
        """
        if not obj :
            default_text = kwargs.pop('default' , _('Не указан'))
            return self._format_field(None , 'foreign_key' , default=default_text , **kwargs)

        # Безопасный доступ к метаданным связанного объекта
        model_name = self._safe_get_model_name(obj)
        app_label = self._safe_get_app_label(obj)

        # Базовые данные
        include_data = kwargs.pop('include_data' , 'compact')
        data = {
            'value' : obj.id ,
            'formatted' : str(obj) ,
            'type' : 'foreign_key' ,
            'is_empty' : False ,
            'model' : model_name ,
            'app' : app_label ,
        }

        # Добавляем данные связанного объекта
        if include_data == 'compact' and hasattr(obj , 'get_compact_data') :
            data['compact'] = obj.get_compact_data()
        elif include_data == 'display' and hasattr(obj , 'get_display_data') :
            data['display'] = obj.get_display_data('badge')
        elif include_data == 'full' and hasattr(obj , 'get_full_data') :
            data['full'] = obj.get_full_data(['form'])

        # Добавляем дополнительные параметры
        for key in ['label' , 'icon' , 'priority' , 'required' , 'help_text'] :
            if key in kwargs :
                data[key] = kwargs[key]

        return data

    def _format_many_to_many(self , queryset , **kwargs) -> Dict[str , Any] :
        """
        Форматирование ManyToMany поля

        Args:
            queryset: QuerySet связанных объектов
            **kwargs: дополнительные параметры
        """
        if not queryset.exists() :
            default_text = kwargs.pop('default' , _('Нет данных'))
            return self._format_field([] , 'many_to_many' , default=default_text , **kwargs)

        items = list(queryset)
        include_data = kwargs.pop('include_data' , 'compact')

        formatted_items = []
        for item in items :
            item_data = {
                'id' : item.id ,
                'name' : str(item) ,
                'model' : self._safe_get_model_name(item) ,
            }

            if include_data == 'compact' and hasattr(item , 'get_compact_data') :
                item_data.update(item.get_compact_data())
            elif include_data == 'display' and hasattr(item , 'get_display_data') :
                item_data['display'] = item.get_display_data('badge')

            formatted_items.append(item_data)

        return self._format_field(
            items ,
            'many_to_many' ,
            formatted=', '.join([str(item) for item in items]) ,
            items=formatted_items ,
            count=len(items) ,
            **kwargs
        )

    def _format_boolean(self , value: bool , **kwargs) -> Dict[str , Any] :
        """
        Форматирование булевого поля
        """
        true_text = kwargs.pop('true_text' , _('Да'))
        false_text = kwargs.pop('false_text' , _('Нет'))

        formatted = true_text if value else false_text
        return self._format_field(
            value ,
            'boolean' ,
            formatted=formatted ,
            **kwargs
        )

    def _format_choice(self , value: str , choices: list , **kwargs) -> Dict[str , Any] :
        """
        Форматирование поля с выбором
        """
        # Преобразуем choices в словарь для поиска
        choices_dict = dict(choices)
        formatted = choices_dict.get(value , value)

        return self._format_field(
            value ,
            'choice' ,
            formatted=formatted ,
            choices=choices ,
            **kwargs
        )

    def _get_base_display_fields(self) -> Dict[str , Dict] :
        """
        Базовые поля для отображения (общие для всех моделей)
        """
        fields = {}

        # Добавляем name, если есть в модели
        if hasattr(self , 'name') :
            fields['name'] = self._format_field(
                self.name ,
                'text' ,
                label=_('Название') ,
                icon='📄' ,
                priority=1
            )

        # Добавляем code, если есть в модели
        if hasattr(self , 'code') :
            fields['code'] = self._format_field(
                self.code ,
                'code' ,
                label=_('Код') ,
                icon='🔢' ,
                priority=2
            )

        # Добавляем is_active, если есть в модели
        if hasattr(self , 'is_active') :
            fields['is_active'] = self._format_field(
                self.is_active ,
                'boolean' ,
                label=_('Статус') ,
                formatted=_('Активен') if self.is_active else _('Неактивен') ,
                icon='✅' if self.is_active else '❌' ,
                priority=100
            )

        # Добавляем description, если есть в модели
        if hasattr(self , 'description') :
            fields['description'] = self._format_field(
                self.description ,
                'text' ,
                label=_('Описание') ,
                icon='📄' ,
                priority=50 ,
                multiline=True
            )

        return fields

    def _get_status_badge(self) -> Dict[str , Any] :
        """
        Получить статус объекта в виде бейджа
        """
        status = 'active'
        text = _('Активен')

        if hasattr(self , 'is_active') and not self.is_active :
            status = 'inactive'
            text = _('Неактивен')
        elif hasattr(self , 'is_deleted') and self.is_deleted :
            status = 'deleted'
            text = _('Удален')
        elif hasattr(self , 'is_published') and not self.is_published :
            status = 'draft'
            text = _('Черновик')

        return {
            'text' : text ,
            'type' : status ,
            'color' : {
                'active' : 'green' ,
                'inactive' : 'gray' ,
                'deleted' : 'red' ,
                'draft' : 'yellow'
            }.get(status , 'blue')
        }

    def _get_actions(self , request=None) -> List[Dict[str , Any]] :
        """
        Получить список действий для объекта
        """
        actions = [
            {
                'label' : _('Редактировать') ,
                'url' : self.get_admin_url() ,
                'icon' : '✏️' ,
                'type' : 'edit' ,
                'permission' : 'change'
            } ,
            {
                'label' : _('Удалить') ,
                'url' : f"{self.get_admin_url()}delete/" ,
                'icon' : '🗑️' ,
                'type' : 'delete' ,
                'permission' : 'delete' ,
                'confirm' : True
            }
        ]

        # Добавляем просмотр, если есть get_absolute_url
        if hasattr(self , 'get_absolute_url') :
            actions.insert(0 , {
                'label' : _('Просмотреть') ,
                'url' : self.get_absolute_url() ,
                'icon' : '👁️' ,
                'type' : 'view' ,
                'external' : True
            })

        return actions

    def _get_metadata_template(self) -> Dict[str , Any] :
        """
        Шаблон метаданных для переопределения в моделях
        """
        return {
            'field_schema' : [] ,
            'validation_rules' : {} ,
            'permissions' : {
                'view' : True ,
                'add' : True ,
                'change' : True ,
                'delete' : True ,
            }
        }

    # ==================== УТИЛИТАРНЫЕ МЕТОДЫ ====================

    def _safe_get_model_name(self , obj=None) :
        """Безопасное получение имени модели"""
        if obj is None :
            obj = self
        try :
            return obj._meta.model_name
        except AttributeError :
            return obj.__class__.__name__.lower()

    def _safe_get_app_label(self , obj=None) :
        """Безопасное получение метки приложения"""
        if obj is None :
            obj = self
        try :
            return obj._meta.app_label
        except AttributeError :
            return 'unknown'

    def _get_model_name(self) :
        """Получить имя модели (alias для совместимости)"""
        return self._safe_get_model_name()

    def _get_app_label(self) :
        """Получить метку приложения (alias для совместимости)"""
        return self._safe_get_app_label()

    def get_admin_url(self) -> str :
        """
        URL в админке Django
        """
        app_label = self._safe_get_app_label()
        model_name = self._safe_get_model_name()
        obj_id = getattr(self , 'id' , '')
        return f"/admin/{app_label}/{model_name}/{obj_id}/change/"

    def get_absolute_url(self) -> str :
        """
        Базовый URL для объекта.
        Переопределите в моделях, если нужно.
        """
        app_label = self._safe_get_app_label()
        model_name = self._safe_get_model_name()
        obj_id = getattr(self , 'id' , '')
        return f"/{app_label}/{model_name}/{obj_id}/"

    def get_api_url(self) -> str :
        """
        URL для API
        """
        app_label = self._safe_get_app_label()
        model_name = self._safe_get_model_name()
        obj_id = getattr(self , 'id' , '')
        return f"/api/{app_label}/{model_name}/{obj_id}/"

    def get_export_data(self , format_type: str = 'csv') -> Dict[str , Any] :
        """
        Данные для экспорта
        """
        data = self.get_compact_data()

        # Добавляем дополнительные поля для экспорта
        if hasattr(self , 'created_at') :
            data['created_at'] = self.created_at.isoformat() if self.created_at else None

        if hasattr(self , 'updated_at') :
            data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None

        # Форматируем для разных типов экспорта
        if format_type == 'csv' :
            # Преобразуем в плоскую структуру для CSV
            flat_data = {}
            for key , value in data.items() :
                if isinstance(value , dict) :
                    for sub_key , sub_value in value.items() :
                        flat_data[f"{key}_{sub_key}"] = sub_value
                else :
                    flat_data[key] = value
            return flat_data

        return data

    def is_editable(self , user=None) -> bool :
        """
        Проверка, можно ли редактировать объект
        """
        if hasattr(self , 'is_active') and not self.is_active :
            return False

        if hasattr(self , 'is_deleted') and self.is_deleted :
            return False

        # Дополнительная логика проверки прав пользователя
        if user and hasattr(self , 'can_edit') :
            return self.can_edit(user)

        return True

    def get_field_value(self , field_name: str , default: Any = None) -> Any :
        """
        Безопасное получение значения поля
        """
        try :
            value = getattr(self , field_name)
            if callable(value) :
                value = value()
            return value
        except (AttributeError , ValueError) :
            return default

    # ==================== МЕТОДЫ ДЛЯ РАБОТЫ С СВЯЗЯМИ ====================

    def get_related_objects(self , relation_name: str , **filters) -> List[Any] :
        """
        Получить связанные объекты
        """
        try :
            if hasattr(self , relation_name) :
                relation = getattr(self , relation_name)
                if hasattr(relation , 'all') :
                    queryset = relation.all()
                    if filters :
                        queryset = queryset.filter(**filters)
                    return list(queryset)
        except Exception :
            pass

        return []

    # ==================== МЕТОДЫ ДЛЯ РАБОТЫ С ПРАВАМИ ====================

    def check_permission(self , permission_type: str , user=None) -> bool :
        """
        Проверка прав доступа
        """
        # Базовая реализация, можно расширить
        if permission_type == 'view' :
            return True

        if permission_type == 'edit' :
            return self.is_editable(user)

        if permission_type == 'delete' :
            if hasattr(self , 'is_deleted') and self.is_deleted :
                return False
            return True

        return True

    # Создаем TypeVar для возвращаемого типа
    T = TypeVar('T', bound='StructuredDataMixin')

    def copy(self: T, save_copy: bool = False, copy_relations: bool = False, **kwargs) -> T:
        """
        Создает копию объекта

        Args:
            save_copy: Сохранить копию в БД (если False - возвращает несохраненный объект)
            copy_relations: Скопировать связанные объекты (ManyToMany и обратные связи)
            **kwargs: Дополнительные параметры для настройки копирования

        Returns:
            Новый объект (сохраненный или нет)

        Example:
            original = SomeModel.objects.get(id=1)
            copy_obj = original.copy(save_copy=True)
            copy_obj.name = f"Копия {original.name}"
            copy_obj.save()
        """
        # Получаем все поля текущего объекта
        all_fields = self._meta.fields

        # Создаем словарь для нового объекта, исключая первичный ключ
        new_data = {}
        for field in all_fields:
            if field.name != self._meta.pk.name:
                value = getattr(self, field.name)

                # Для ForeignKey полей
                if isinstance(field, models.ForeignKey):
                    if value is not None:
                        new_data[field.name] = value
                    else:
                        new_data[field.name] = None
                else:
                    new_data[field.name] = value

        # Применяем кастомные преобразования для полей из kwargs
        for field_name, transform_func in kwargs.get('field_transforms', {}).items():
            if field_name in new_data:
                new_data[field_name] = transform_func(new_data[field_name], self)

        # Создаем новый объект
        new_copy = self.__class__(**new_data)

        if save_copy:
            new_copy.save()

            # Копируем связанные объекты если нужно
            if copy_relations:
                self._copy_relations(new_copy)

        return new_copy

    def _copy_relations(self, new_copy: Any) -> None:
        """
        Копирует связанные объекты (переопределите в дочерних моделях при необходимости)

        Args:
            new_copy: Сохраненная копия объекта
        """
        # Базовый метод - ничего не делает
        # Переопределите в конкретной модели для копирования связей
        pass

    def _get_copy_field_transforms(self) -> Dict[str, Callable]:
        """
        Возвращает словарь с функциями преобразования полей при копировании

        Returns:
            dict: {field_name: transform_function}

        Example:
            def _get_copy_field_transforms(self):
                return {
                    'name': lambda val, obj: f"{val} (копия)",
                    'code': lambda val, obj: f"{val}_copy",
                    'sorting_order': lambda val, obj: val + 1,
                }
        """
        # Базовые преобразования для стандартных полей
        transforms = {}

        if hasattr(self, 'name'):
            transforms['name'] = lambda val, obj: f"{val} (копия)"

        if hasattr(self, 'code'):
            transforms['code'] = lambda val, obj: f"{val}_copy"

        if hasattr(self, 'sorting_order'):
            transforms['sorting_order'] = lambda val, obj: val + 1

        return transforms

    def create_copy(self: T, save_copy: bool = True, copy_relations: bool = False) -> T:
        """
        Упрощенный метод для создания копии с сохранением

        Args:
            save_copy: Сохранить копию в БД
            copy_relations: Скопировать связанные объекты

        Returns:
            Новый объект
        """
        transforms = self._get_copy_field_transforms()
        return self.copy(
            save_copy=save_copy,
            copy_relations=copy_relations,
            field_transforms=transforms
        )

class TimestampMixin(models.Model) :
    """
    Миксин для временных меток создания/обновления
    """
    created_at = models.DateTimeField(
        auto_now_add=True ,
        verbose_name=_("Дата создания") ,
        editable=False
    )

    updated_at = models.DateTimeField(
        auto_now=True ,
        verbose_name=_("Дата обновления") ,
        editable=False
    )

    class Meta :
        abstract = True


class SoftDeleteMixin(models.Model) :
    """
    Миксин для мягкого удаления
    """
    is_deleted = models.BooleanField(
        default=False ,
        verbose_name=_("Удален") ,
        help_text=_("Объект помечен как удаленный")
    )

    deleted_at = models.DateTimeField(
        null=True ,
        blank=True ,
        verbose_name=_("Дата удаления")
    )

    class Meta :
        abstract = True

    def delete(self , using=None , soft: bool = True) :
        """Мягкое удаление"""
        if soft :
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()
        else :
            super().delete(using=using)

    def restore(self) :
        """Восстановление удаленного"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()

class AdminStructuredDataMixinCopyMixin :
    """Миксин для добавления action копирования"""

    @admin.action(description=_("Копировать выбранные объекты"))
    def copy_objects(self, request, queryset):
        copied_count = 0
        errors = []

        for obj in queryset:
            try:
                if hasattr(obj, 'create_copy'):
                    new_obj = obj.create_copy()
                elif hasattr(obj, 'copy'):
                    new_obj = obj.copy(save_copy=True)
                else:
                    errors.append(f"{obj} (нет метода copy)")
                    continue

                copied_count += 1
                logger.info(f"Скопирован {obj} -> {new_obj}")

            except Exception as e:
                errors.append(f"{obj}: {str(e)}")
                logger.error(f"Ошибка копирования {obj}: {e}")

        if copied_count :
            # Добавляем подсказку типа для IDE
            # noinspection PyUnresolvedReferences
            self.message_user(request , f"Скопировано {copied_count} объектов" , messages.SUCCESS)
        if errors :
            # noinspection PyUnresolvedReferences
            self.message_user(request , f"Ошибки: {', '.join(errors[:3])}" , messages.WARNING)

class TextDescriptionMixin:
    """Миксин для генерации текстового описания"""

    def get_text_description(self) -> str:
        """
        Генерирует текстовое описание с подстановкой значений.
        Должен быть переопределен в каждой модели.
        """
        raise NotImplementedError(f"get_text_description not implemented for {self.__class__.__name__}")

class OptionListToSelectMixin:
    @classmethod
    def get_for_select(cls, active_only: bool = True) -> List[Dict]:
        queryset = cls.objects.all()

        if active_only and hasattr(cls, 'is_active'):
            queryset = queryset.filter(is_active=True)

        return [{'id': obj.id, 'name': str(obj)} for obj in queryset]

class GetChoicesMixin:
    """
    Миксин для заполнения список кортежей для использования в выпадающем списке
    Не требует model_line и других зависимостей.
    """

    @classmethod
    def get_choices(cls) :
        """
        Возвращает список кортежей для использования в выпадающем списке
        Returns: [(id, name), ...] или [(0, "— Выберите —"), (id, name), ...]
        """
        choices = cls.objects.filter(is_active=True).order_by('sorting_order' , 'name')
        return [(item.id , item.name) for item in choices]

    @classmethod
    def get_select_choices(cls , include_empty=True) :
        """
        Возвращает список кортежей с пустым значением для selectbox
        Args:
            include_empty: добавить ли пустой вариант "-- Выберите --"
        Returns: [(0, "— Выберите —"), (id, name), ...] или [(id, name), ...]
        """
        choices = cls.get_choices()

        if include_empty :
            return [(0 , "— Выберите —")] + choices

        return choices

    @classmethod
    def get_choice_by_id(cls , choice_id) :
        """ Получить название по ID """
        if not choice_id :
            return None

        try :
            item = cls.objects.get(id=choice_id , is_active=True)
            return item.name
        except cls.DoesNotExist :
            return None


class CopyMixin:
    """
    Миксин для копирования моделей.
    Добавляет метод copy() для создания копии объекта.
    """

    def copy(self, suffix=" Копия", preserve_code=False, reset_fields=None, deep_copy_fields=None):
        """
        Создает копию объекта.

        Args:
            suffix: Суффикс, добавляемый к полю code (по умолчанию " Копия")
            preserve_code: Если True, не изменять поле code (по умолчанию False)
            reset_fields: Список полей, которые нужно сбросить (например, ['sorting_order', 'is_active'])
            deep_copy_fields: Список полей, для которых нужен deep copy (например, ['extra_params']).
                      Также автоматически определяется для JSONField.
        Returns:
            Model: Новая копия объекта
        """
        # Создаем копию объекта
        copied_obj = self.__class__()

        # Поля для сброса по умолчанию
        if reset_fields is None:
            reset_fields = ['sorting_order', 'is_active']

        # Копируем все поля
        for field in self._meta.fields:
            field_name = field.name

            # Пропускаем первичный ключ
            if field_name == 'id':
                continue

            # Обработка поля code
            if field_name == 'code' and not preserve_code:
                original_code = getattr(self, field_name)
                if original_code:
                    copied_value = f"{original_code}{suffix}"
                else:
                    copied_value = f"{getattr(self, 'name', '')}{suffix}"
                setattr(copied_obj, field_name, copied_value)

            # Сброс указанных полей
            elif field_name in reset_fields:
                # Для булевых полей сбрасываем в True (активно по умолчанию)
                if isinstance(field, models.BooleanField):
                    setattr(copied_obj, field_name, True)
                # Для числовых полей сбрасываем в 0
                elif isinstance(field, (models.IntegerField, models.FloatField, models.DecimalField)):
                    setattr(copied_obj, field_name, 0)
                else:
                    setattr(copied_obj, field_name, None)

            # OneToOne на SKU не копируем — sync_sku() пересоздаст привязку
            elif field_name == 'sku':
                setattr(copied_obj, field_name, None)

            # Копируем остальные поля
            else:
                value = getattr(self, field_name)
                # Deep copy для mutable-полей (JSONField, dict, list)
                if self._should_deep_copy(field, field_name, value, deep_copy_fields):
                    value = copy.deepcopy(value)
                setattr(copied_obj, field_name, value)

        # Сохраняем копию
        copied_obj.save()

        # Копируем ManyToMany связи (если есть)
        for m2m_field in self._meta.many_to_many:
            getattr(copied_obj, m2m_field.name).set(getattr(self, m2m_field.name).all())

        # Вызываем хук для специализированных связей (exd через through-таблицу и т.п.)
        self._copy_custom_relations(copied_obj)

        return copied_obj

    def _should_deep_copy(self, field, field_name, value, deep_copy_fields):
        """
        Определяет, нужно ли делать deep copy для поля.
        """
        if value is None:
            return False
        # Явно указанные поля
        if deep_copy_fields and field_name in deep_copy_fields:
            return isinstance(value, (dict, list))
        # Автоопределение: JSONField
        if isinstance(field, models.JSONField):
            return isinstance(value, (dict, list))
        return False

    def _copy_custom_relations(self, new_copy):
        """
        Хук для копирования специализированных связей (exd через through-таблицу и т.п.).
        Переопределите в модели при необходимости.
        """
        pass

class AdminCopyMixin:
    """
    Миксин для админки с настройками копирования.
    """

    # Можно переопределить в дочернем классе
    copy_action_description = "📋 Копировать выбранные объекты"
    copy_suffix = " Копия"

    def copy_selected_objects(self, request, queryset):
        """
        Действие для копирования выбранных объектов
        Использование в admin.py:
        class FilterRegulatorAdmin(AdminCopyMixin, admin.ModelAdmin):
            list_display = ['name', 'code', 'sorting_order', 'is_active']
            actions = ['copy_selected_objects']  # Действие уже есть в миксине
        """

        copied_count = 0
        errors = []

        for obj in queryset:
            try:
                if hasattr(obj, 'copy'):
                    # Если у модели есть метод copy - используем его
                    obj.copy()
                else:
                    # Стандартное копирование
                    obj.pk = None
                    obj.save()
                copied_count += 1
            except Exception as e:
                obj_name = getattr(obj, 'name', getattr(obj, 'title', str(obj)))
                errors.append(f"{obj_name}: {str(e)}")

        # Сообщаем о результате
        if copied_count:
            self.message_user(
                request,
                f"✅ Успешно скопировано: {copied_count}",
                level='SUCCESS'
            )

        if errors:
            self.message_user(
                request,
                f"⚠️ Ошибки ({len(errors)}): {'; '.join(errors[:5])}",
                level='ERROR'
            )

    copy_selected_objects.short_description = copy_action_description


class CatalogDictMixin:
    """
    Миксин для моделей каталога — структурированная сериализация в словарь.

    Использует единый метод ``to_dict()`` для трёх режимов выдачи:
      - ``get_field_meta()``     — метаданные полей (label, group, unit, type)
      - ``to_values_dict()``     — только значения (для списков)
      - ``to_dict()``            — полная структура с секциями (для деталки)

    ``to_dict()`` должен возвращать словарь с ключами:
      - ``template_vars``   — плоский словарь {key: value} для шаблонов описаний
      - ``sections``        — список секций [{key, title, type, order, data/groups}]

    Поддерживает gettext-переводы через ``django.utils.translation.gettext_lazy``.
    При запросе с ``?lang=zh`` Django-мидлварь активирует нужную локаль.
    """

    def to_dict(self) -> dict:
        raise NotImplementedError(
            f"{self.__class__.__name__} должен реализовать to_dict()"
        )

    def _get_image_url(self, img):
        if not img:
            return None
        return img.get_serve_url() if hasattr(img, 'get_serve_url') else None

    def _get_doc_url(self, doc):
        if not doc:
            return None
        return doc.get_serve_url() if hasattr(doc, 'get_serve_url') else None

    # ═══════════════════════════════════════════════════════════════
    # Шаблон для новых каталогов — см. CATALOG_PATTERN.md
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def get_field_meta(cls) -> dict:
        """
        Извлекает плоский словарь field_key -> {label, group, unit, type} из sections.

        Вызывается на классе (без инстанса) — создаёт dummy-объект.
        """
        dummy = cls()
        data = dummy.to_dict()
        meta = {}
        for section in data.get("sections", []):
            if section.get("type") == "specs":
                for group in section.get("groups", []):
                    for field in group.get("fields", []):
                        meta[field["key"]] = {
                            "label": field["label"],
                            "group": group.get("title", ""),
                            "unit": field.get("unit", ""),
                            "type": field.get("type", "text"),
                            "order": field.get("order", 0),
                        }
        return meta

    def to_values_dict(self) -> dict:
        """
        Только значения полей (без метаданных) — для списков.

        Возвращает:
            {id, code, name, values: {key: value}, images, model_line, sku, ...}
        """
        data = self.to_dict()
        values = {}
        for section in data.get("sections", []):
            if section.get("type") == "specs":
                for group in section.get("groups", []):
                    for field in group.get("fields", []):
                        values[field["key"]] = field["value"]
        return {
            "id": data.get("id"),
            "code": data.get("code"),
            "name": data.get("name"),
            "image_alt": data.get("image_alt", ""),
            "template_vars": data.get("template_vars", {}),
            "values": values,
            "images": next(
                (s["data"] for s in data.get("sections", [])
                 if s.get("type") == "gallery"),
                [],
            ),
            "model_line": data.get("model_line"),
            "sku": data.get("sku"),
        }

    @staticmethod
    def build_schema(data: dict, *, price_data: dict = None,
                     category_name: str = None) -> dict:
        """
        Генерирует Schema.org Product из структуры to_dict().

        Читает:
          - data["code"], data["name"]               -> name, sku, mpn
          - data["template_vars"]["brand_name"]       -> Brand
          - data["sections"][type=gallery]            -> image
          - data["sections"][type=text]               -> description
          - price_data                                -> Offer
        """
        tv = data.get("template_vars", {}) or {}

        # Изображения
        images = []
        for s in data.get("sections", []):
            if s.get("type") == "gallery":
                images = [img["url"] for img in s.get("data", []) if img.get("url")]
                break

        # Описание
        description = ""
        for s in data.get("sections", []):
            if s.get("type") == "text" and s.get("data"):
                description = s["data"]
                break

        schema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": tv.get("name") or data.get("name", ""),
            "sku": tv.get("code") or data.get("code", ""),
            "mpn": tv.get("code") or data.get("code", ""),
            "image": images[0] if images else None,
            "description": description or None,
            "brand": (
                {"@type": "Brand", "name": tv["brand_name"]}
                if tv.get("brand_name") else None
            ),
            "category": str(category_name) if category_name else None,
            "offers": (
                {
                    "@type": "Offer",
                    "priceCurrency": price_data.get("currency", "USD") if price_data else "USD",
                    "price": str(price_data.get("price", "")),
                    "availability": "https://schema.org/InStock",
                }
                if price_data else None
            ),
        }

        return {k: v for k, v in schema.items() if v is not None}