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

logger = logging.getLogger(__name__)


class TemplateMixin:
    """
    Миксин для генерации названий и описаний из шаблонов.
    Включает в себя методы получения значений по путям (_get_value).
    """

    # === МЕТОДЫ ПОЛУЧЕНИЯ ЗНАЧЕНИЙ (поля, связи, JSON) ===
    def _get_value(self, field_path: str) -> str:
        """Универсальное получение значения по пути (поля, связи, JSON)."""
        try:
            return self._get_field_value(field_path)
        except Exception as e:
            logger.error(f"Ошибка получения {field_path}: {e}")
            return ""

    def _get_field_value(self, field_path: str) -> str:
        """Реализация получения значения (без вызова методов)."""
        current_obj = self
        parts = field_path.split('__')
        for part in parts:
            if '.' in part:
                json_field, json_key = part.split('.', 1)
                if hasattr(current_obj, json_field):
                    current_obj = getattr(current_obj, json_field)
                    if isinstance(current_obj, dict):
                        current_obj = current_obj.get(json_key, '')
                    else:
                        return ""
                else:
                    return ""
            else:
                if hasattr(current_obj, part):
                    current_obj = getattr(current_obj, part)
                    if current_obj is None:
                        return ""
                else:
                    return ""
        return str(current_obj) if current_obj is not None else ""

    # === ПОЛУЧЕНИЕ ШАБЛОНОВ ИЗ ИСТОЧНИКА ===
    def _get_name_template_source(self):
        """Переопределить в модели: вернуть шаблон названия или None."""
        return None

    def _get_description_template_source(self):
        """Переопределить в модели: вернуть шаблон описания или None."""
        return None

    # === ДЕФОЛТНЫЕ ШАБЛОНЫ ===
    def _get_default_name_template(self) -> str:
        return "{model_code}"

    def _get_default_description_template(self) -> str:
        return "{model_code}"

    # === ИТОГОВЫЕ ШАБЛОНЫ ===
    @property
    def name_template(self) -> str:
        return self._get_name_template_source() or self._get_default_name_template()

    @property
    def description_template(self) -> str:
        return self._get_description_template_source() or self._get_default_description_template()

    # === СЛОВАРЬ ДЛЯ ПОДСТАНОВКИ ===
    def _get_data_dict(self) -> Dict[str, str]:
        """Переопределить в модели: вернуть словарь {плейсхолдер: значение/путь}."""
        return {
            '{model_code}': '$code',
        }

    # === ЗАПОЛНЕНИЕ ШАБЛОНА ===
    def _fill_template(self, template: str, data_dict: Dict[str, str] = None) -> str:
        import re
        if not template:
            return ""
        if data_dict is None:
            data_dict = self._get_data_dict()
        result = template
        for placeholder, value in data_dict.items():
            if isinstance(value, str) and value.startswith('$'):
                path = value[1:]
                value = self._get_value(path)
            result = result.replace(placeholder, str(value) if value is not None else "")
        # Удаляем оставшиеся незамененные плейсхолдеры
        result = re.sub(r'\{[^{}]+\}', '', result)
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

class ValueGetterMixin :
    """
    Миксин для универсального получения значений из полей модели:
    - Обычные поля
    - Связанные поля через __
    - JSON поля через .
    - Комбинации
    - Вызов методов с параметрами (для M2M и других)
    """

    def _get_value(self , field_path: str) -> str :
        """
        Универсальное получение значения:
        - Обычные поля: 'code'
        - Связи через __: 'body__material'
        - JSON поля через .: 'extra_params.ip_rating'
        - Комбинация: 'body__extra_params.cable_glands_holes'
        - Вызов методов: 'get_sensors_list("{name}")'
        - Вызов методов с параметрами: 'body.get_cable_glands_holes("Отв.{name}", ", ", " или ")'
        """
        print(f"[DEBUG] _get_value: field_path='{field_path}'")
        try :
            # Проверяем, есть ли вызов метода с параметрами
            # if '(' in field_path and ')' in field_path :
            #     return self._call_method_from_path(field_path)

            # Обычная обработка (поля, связи, JSON)
            return self._get_field_value(field_path)

        except Exception as e :
            logger.error(f"Ошибка получения {field_path}: {e}")
            return ""


    # def _call_method_from_path(self , field_path: str) -> str :
    #     """
    #     Вызывает метод из строки пути.
    #
    #     Поддерживаемые форматы:
    #     - 'method_name("{param1}")'
    #     - 'object.method_name("{param1}", "{param2}")'
    #     - 'object__subobject.method_name("{param1}")'
    #
    #     Примеры:
    #     - 'get_sensors_list("{name}")'
    #     - 'body.get_cable_glands_holes("Отв.{name}", ", ", " или ")'
    #     - 'model_line__brand.get_full_name("{code}")'
    #     """
    #     import re
    #
    #     print(f"[DEBUG] _call_method_from_path: field_path='{field_path}'")
    #
    #     # Разделяем на часть до скобок и параметры
    #     match = re.match(r'^([^(]+)\((.*)\)$' , field_path)
    #     if not match :
    #         print(f"[DEBUG] не удалось распарсить: нет скобок")
    #         return ""
    #
    #     method_path = match.group(1)
    #     params_str = match.group(2)
    #
    #     print(f"[DEBUG] method_path: '{method_path}'")
    #     print(f"[DEBUG] params_str: '{params_str}'")
    #
    #     # Парсим параметры (строки в кавычках)
    #     # Шаблон для поиска строк: '...' или "..."
    #     params = re.findall(r"'([^']*)'|\"([^\"]*)\"" , params_str)
    #     params = [p[0] or p[1] for p in params]
    #     print(f"[DEBUG] распарсенные параметры: {params}")
    #
    #     # Определяем объект, у которого вызываем метод
    #     # Если в method_path нет точки - вызываем на self
    #     if '.' not in method_path :
    #         current_obj = self
    #         method_name = method_path
    #         print(f"[DEBUG] вызываем метод {method_name} на self")
    #     else :
    #         # Разбираем путь к объекту
    #         parts = method_path.split('.')
    #         current_obj = self
    #         for part in parts[:-1] :
    #             # Поддерживаем __ для связей
    #             for subpart in part.split('__') :
    #                 if hasattr(current_obj , subpart) :
    #                     current_obj = getattr(current_obj , subpart)
    #                     print(f"[DEBUG] перешли к {subpart}: {current_obj}")
    #                     if current_obj is None :
    #                         print(f"[DEBUG] current_obj is None")
    #                         return ""
    #                 else :
    #                     print(f"[DEBUG] у {current_obj} нет атрибута {subpart}")
    #                     return ""
    #         method_name = parts[-1]
    #         print(f"[DEBUG] вызываем метод {method_name} на объекте {current_obj}")
    #
    #     # Вызываем метод
    #     if hasattr(current_obj , method_name) :
    #         method = getattr(current_obj , method_name)
    #         if callable(method) :
    #             print(f"[DEBUG] вызываем метод с параметрами {params}")
    #             result = method(*params)
    #             print(f"[DEBUG] результат: '{result}'")
    #             return result
    #         else :
    #             print(f"[DEBUG] {method_name} не является вызываемым")
    #     else :
    #         print(f"[DEBUG] у {current_obj} нет метода {method_name}")
    #
    #     return ""

    def _get_field_value(self , field_path: str) -> str :
        """
        Получает значение обычного поля, связи или JSON.

        Поддерживаемые форматы:
        - 'code' - простое поле
        - 'body__material' - связь через __
        - 'extra_params.ip_rating' - JSON поле через .
        - 'body__extra_params.cable_glands_holes' - комбинация
        """
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


class TemplateFillerMixin:
    """
    Миксин для заполнения шаблонов значениями из полей модели.
    Не требует model_line и других зависимостей.
    """

    def _get_data_dict(self) -> Dict[str, str]:
        """
        Должен быть переопределен в модели.
        Возвращает словарь {плейсхолдер: путь_к_атрибуту}
        """
        return {}

    def _get_value(self, attr_path: str) -> str:
        """
        Получает значение по вложенному пути.
        Поддерживает:
        - Обычные поля: 'code'
        - Связи через __: 'brand__name'
        - JSON поля через .: 'extra_params.material'
        """
        try:
            current = self
            # Заменяем . на __ для единообразия
            path = attr_path.replace('.', '__')
            for part in path.split('__'):
                if hasattr(current, part):
                    current = getattr(current, part)
                    if current is None:
                        return ""
                elif isinstance(current, dict) and part in current:
                    current = current.get(part, "")
                else:
                    return ""
            return str(current) if current is not None else ""
        except Exception:
            return ""
    def _get_model_meta_name(self) -> str:
        """Возвращает имя модели для логов"""
        return self.__class__.__name__

    def _fill_template(self, template_str: str, placeholder_to_attr: Dict[str, str] = None, hide_code: bool = False) -> str:
        """
        Заполняет шаблон значениями из словаря.

        Args:
            template_str: шаблон с плейсхолдерами {placeholder}
            placeholder_to_attr: словарь соответствий (если None, то используется self._get_data_dict())
            hide_code: игнорируется в этом миксине, оставлен для совместимости

        Returns:
            Заполненная строка
        """
        if not template_str:
            return ""

        if placeholder_to_attr is None:
            placeholder_to_attr = self._get_data_dict()

        result = template_str
        for placeholder, attr_path in placeholder_to_attr.items():
            value = self._get_value(attr_path)
            result = result.replace(placeholder, str(value) if value is not None else "")

        return result


class TemplateGeneratorMixin(TemplateFillerMixin):
    """
    Миксин для генерации названий и описаний из шаблонов model_line.
    Наследует TemplateFillerMixin для базовой функциональности заполнения.
    """

    def generated_model_name_description(self, name_or_description: str, hide_code: bool = False) -> str:
        """
        Сгенерировать название или описание по шаблону из model_line

        Args:
            name_or_description: 'name' или 'description' - что генерировать
            hide_code: скрыть model_code при генерации
        """
        model_name = self._get_model_meta_name()

        if not self.model_line:
            return self.name or ""

        # Выбираем шаблон
        if name_or_description == 'name':
            template = self.model_line.name_template
            if not template or not template.strip():
                template = self._get_default_name_template()
                if not template or not template.strip():
                    logger.error(
                        f'Ошибка при формировании названия в {model_name} - '
                        f'нет шаблона названия (ни в model_line, ни дефолтного)'
                    )
                    return self.name or ""
        else:
            template = self.model_line.description_template
            if not template or not template.strip():
                template = self._get_default_description_template()
                if not template or not template.strip():
                    logger.error(
                        f'Ошибка при формировании описания в {model_name} - '
                        f'нет шаблона описания (ни в model_line, ни дефолтного)'
                    )
                    return self.description or ""

        # Получаем словарь соответствий
        placeholder_to_attr = self._get_data_dict()

        # Заполняем шаблон
        result = self._fill_template(template, placeholder_to_attr, hide_code)

        return result

    def _process_m2m_field(self, related_manager, item_template: str, separator: str = ", ",
                           last_separator: str = None) -> str:
        """
        Универсальный метод для обработки M2M полей

        Args:
            related_manager: related менеджер M2M поля (например, self.sensor_components)
            item_template: шаблон для каждого элемента (например '{name}', '{code} {name}')
            separator: разделитель между элементами
            last_separator: последний разделитель (если None, то используется separator)

        Returns:
            Строка с объединенными элементами
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.debug(f"_process_m2m_field: начало обработки")
        logger.debug(f"  item_template: {item_template}")
        logger.debug(f"  separator: {separator}")
        logger.debug(f"  last_separator: {last_separator}")

        items = related_manager.all()
        logger.debug(f"  количество items: {items.count()}")

        if not items:
            logger.debug("  items пуст, возвращаем пустую строку")
            return ""

        result_items = []
        for idx, item in enumerate(items):
            logger.debug(f"  обработка item {idx}: {item}")
            logger.debug(f"    тип item: {type(item).__name__}")

            # Если у элемента есть метод _fill_template - используем его
            if hasattr(item, '_fill_template'):
                logger.debug(f"    у item есть _fill_template")
                filled = item._fill_template(item_template)
                logger.debug(f"    filled после _fill_template: {filled}")
            else:
                logger.debug(f"    у item НЕТ _fill_template, используем простую подстановку")
                # Простая подстановка для обычных моделей
                filled = item_template
                for attr in ['name', 'code', 'full_code', 'description']:
                    if f'{{{attr}}}' in filled:
                        value = getattr(item, attr, '')
                        filled = filled.replace(f'{{{attr}}}', str(value) if value else '')
                        logger.debug(f"      заменен {{{attr}}} на '{value}'")
                logger.debug(f"    filled после простой подстановки: {filled}")

            result_items.append(filled)

        # Объединяем с разделителями
        if len(result_items) == 1:
            result = result_items[0]
            logger.debug(f"  один элемент, результат: {result}")
            return result
        elif len(result_items) == 2 and last_separator:
            result = f"{result_items[0]} {last_separator} {result_items[1]}"
            logger.debug(f"  два элемента с last_separator, результат: {result}")
            return result
        elif len(result_items) > 2 and last_separator:
            result = f"{', '.join(result_items[:-1])} {last_separator} {result_items[-1]}"
            logger.debug(f"  больше двух элементов с last_separator, результат: {result}")
            return result
        else:
            result = separator.join(result_items)
            logger.debug(f"  объединение с separator, результат: {result}")
            return result



    def _get_default_name_template(self) -> str:
        """Должен быть переопределен в модели"""
        return "{model_code}"

    def _get_default_description_template(self) -> str:
        """Должен быть переопределен в модели"""
        return "{model_code}"

    def _get_data_dict(self) -> Dict[str, str]:
        """
        Должен быть переопределен в модели.
        Возвращает словарь соответствий плейсхолдеров и путей к атрибутам.
        """
        return {
            '{model_code}': 'code',
        }

    def update_name_from_template(self):
        """Обновить название из шаблона"""
        print(f'update_name_from_template from TemplateGeneratorMixin')
        if self.model_line and self.model_line.name_template:
            generated_name = self.generated_model_name_description('name')
            if generated_name:
                self.name = generated_name
                return True
        return False

    def update_description_from_template(self):
        """Обновить описание из шаблона"""
        if self.model_line and self.model_line.description_template:
            generated_description = self.generated_model_name_description('description')
            if generated_description:
                self.description = generated_description
                return True
        return False

    def update_name_and_description_from_templates(self):
        """Обновить название и описание из шаблонов"""
        name_updated = self.update_name_from_template()
        description_updated = self.update_description_from_template()
        return name_updated or description_updated

    def save(self, *args, **kwargs):
        """При сохранении обновляем название и описание из шаблонов, если не указано в параметрах skip_auto_generate=True"""
        skip_auto_generate = kwargs.pop('skip_auto_generate', False)
        # print(f'save from TemplateGeneratorMixin. skip_auto_generate={skip_auto_generate}')
        if not skip_auto_generate:
            self.update_name_and_description_from_templates()
        super().save(*args, **kwargs)


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
        print(f"[DEBUG] save: name='{self._get_model_name()}'")
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