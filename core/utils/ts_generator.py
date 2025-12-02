# core/utils/ts_generator.py
"""
Генератор TypeScript интерфейсов из Django моделей.
Безопасная версия с проверкой импортов.
"""

import os
import json
import inspect
from typing import Dict , List , Any , Optional , Set , Tuple
from django.apps import apps
from django.db.models import Model
from django.core.validators import MaxLengthValidator , MinLengthValidator , RegexValidator


class TypeScriptGenerator :
    """Генератор TypeScript интерфейсов и типов"""

    def __init__(self , output_dir: str = None , include_apps: List[str] = None) :
        """
        Args:
            output_dir: Директория для сохранения файлов
            include_apps: Список приложений для обработки (если None - все)
        """
        self.output_dir = output_dir
        self.include_apps = include_apps
        self.generated_interfaces: Set[str] = set()

        # Инициализируем выходную директорию
        if not self.output_dir :
            self._init_output_dir()

    def _init_output_dir(self) :
        """Инициализация выходной директории"""
        from django.conf import settings

        base_dir = settings.BASE_DIR

        # Пробуем разные варианты
        possible_paths = [
            os.path.join(base_dir , 'frontend/src/types/auto-generated') ,
            os.path.join(base_dir , '../frontend/src/types/auto-generated') ,
            os.path.join(base_dir , 'types/auto-generated') ,
            os.path.join(base_dir , 'frontend/types/auto-generated') ,
        ]

        for path in possible_paths :
            if os.path.exists(os.path.dirname(path)) :
                self.output_dir = path
                break

        if not self.output_dir :
            # Создаем в корне
            self.output_dir = os.path.join(base_dir , 'types/auto-generated')

        os.makedirs(self.output_dir , exist_ok=True)

    def _get_field_type_mapping(self , field) -> Tuple[str , str] :
        """
        Определяет TypeScript тип для Django поля.

        Returns:
            Tuple (typescript_type, field_class_name)
        """
        field_class_name = field.__class__.__name__

        # Маппинг типов
        type_mapping = {
            'CharField' : 'string' ,
            'TextField' : 'string' ,
            'IntegerField' : 'number' ,
            'BigIntegerField' : 'number' ,
            'SmallIntegerField' : 'number' ,
            'PositiveIntegerField' : 'number' ,
            'PositiveSmallIntegerField' : 'number' ,
            'BooleanField' : 'boolean' ,
            'NullBooleanField' : 'boolean | null' ,
            'DateField' : 'string' ,  # ISO date
            'DateTimeField' : 'string' ,  # ISO datetime
            'TimeField' : 'string' ,
            'DurationField' : 'string' ,
            'FloatField' : 'number' ,
            'DecimalField' : 'number' ,
            'EmailField' : 'string' ,
            'URLField' : 'string' ,
            'SlugField' : 'string' ,
            'FilePathField' : 'string' ,
            'FileField' : 'string' ,
            'ImageField' : 'string' ,
            'UUIDField' : 'string' ,
            'IPAddressField' : 'string' ,
            'GenericIPAddressField' : 'string' ,
        }

        # Специальная обработка для некоторых полей
        if field_class_name in ['ForeignKey' , 'OneToOneField'] :
            # Пытаемся получить связанную модель
            if hasattr(field , 'related_model') and field.related_model :
                related_model_name = field.related_model.__name__
                return f'I{related_model_name} | null' , field_class_name
            else :
                return 'number | null' , field_class_name

        elif field_class_name == 'ManyToManyField' :
            if hasattr(field , 'related_model') and field.related_model :
                related_model_name = field.related_model.__name__
                return f'I{related_model_name}[]' , field_class_name
            else :
                return 'any[]' , field_class_name

        elif field_class_name == 'JSONField' :
            return 'any' , field_class_name

        # Пытаемся определить по внутреннему типу
        if hasattr(field , 'get_internal_type') :
            internal_type = field.get_internal_type()
            if internal_type in type_mapping :
                return type_mapping[internal_type] , internal_type

        # По умолчанию
        return type_mapping.get(field_class_name , 'any') , field_class_name

    def _get_base_fields(self) -> Dict[str , str] :
        """Базовые поля для всех моделей"""
        return {
            'id' : 'number' ,
            'created_at' : 'string' ,
            'updated_at' : 'string' ,
            'is_active' : 'boolean' ,
            'sorting_order' : 'number' ,
            '_str' : 'string' ,  # для __str__ метода
        }

    def _get_validators_info(self , field) -> str :
        """Информация о валидаторах поля"""
        validators = []

        if hasattr(field , 'validators') :
            for validator in field.validators :
                if hasattr(validator , '__class__') :
                    validator_name = validator.__class__.__name__

                    if validator_name == 'MaxLengthValidator' and hasattr(validator , 'limit_value') :
                        validators.append(f"max_length={validator.limit_value}")
                    elif validator_name == 'MinLengthValidator' and hasattr(validator , 'limit_value') :
                        validators.append(f"min_length={validator.limit_value}")
                    elif validator_name == 'RegexValidator' and hasattr(validator , 'regex') :
                        regex = validator.regex.pattern
                        if len(regex) > 30 :
                            regex = regex[:30] + "..."
                        validators.append(f"regex={regex}")

        # Проверяем max_length напрямую
        if hasattr(field , 'max_length') and field.max_length :
            validators.append(f"max_length={field.max_length}")

        return ", ".join(validators) if validators else ""

    def _get_field_info(self , field) -> Dict[str , Any] :
        """Получить информацию о поле для TypeScript"""
        ts_type , field_class = self._get_field_type_mapping(field)

        # Определяем optional
        is_optional = False
        if hasattr(field , 'null') :
            is_optional = field.null
        if hasattr(field , 'blank') :
            is_optional = is_optional or field.blank

        optional_mark = "?" if is_optional else ""

        # Собираем комментарий
        comment_parts = []

        if hasattr(field , 'verbose_name') and field.verbose_name :
            comment_parts.append(str(field.verbose_name))

        # Длина для строковых полей
        if hasattr(field , 'max_length') and field.max_length :
            comment_parts.append(f"max: {field.max_length}")

        if hasattr(field , 'help_text') and field.help_text :
            comment_parts.append(str(field.help_text))

        # Валидаторы
        validators_info = self._get_validators_info(field)
        if validators_info :
            comment_parts.append(f"validators: {validators_info}")

        # Choices
        if hasattr(field , 'choices') and field.choices :
            choices_count = len(field.choices)
            comment_parts.append(f"choices: {choices_count} options")

        comment = f" // {'; '.join(comment_parts)}" if comment_parts else ""

        return {
            'name' : field.name ,
            'type' : f"{ts_type}{comment}" ,
            'raw_type' : ts_type ,
            'optional' : optional_mark ,
            'field_class' : field_class ,
        }

    def _get_all_models(self) -> List[Model] :
        """Получить все модели для генерации"""
        all_models = []

        for app_config in apps.get_app_configs() :
            if self.include_apps and app_config.label not in self.include_apps :
                continue

            for model in app_config.get_models() :
                # Пропускаем абстрактные модели и системные модели
                if model._meta.abstract :
                    continue

                # Пропускаем модели Django
                if model._meta.app_label in ['auth' , 'admin' , 'sessions' , 'contenttypes'] :
                    continue

                # Проверяем, есть ли у модели нужные методы
                if (hasattr(model , 'get_compact_data') or
                        hasattr(model , 'get_display_data') or
                        hasattr(model , 'get_full_data')) :
                    all_models.append(model)
                else :
                    # Добавляем все модели для полноты
                    all_models.append(model)

        return all_models

    def generate_all(self) -> Dict[str , str] :
        """
        Генерирует все TypeScript файлы.

        Returns:
            Dict с путями файлов и их содержимым
        """
        # Собираем все модели
        all_models = self._get_all_models()

        # Генерируем файлы
        models_ts = self._generate_models_ts(all_models)
        enums_ts = self._generate_enums_ts(all_models)
        index_ts = self._generate_index_ts()

        # Сохраняем файлы
        files_content = {
            'models' : models_ts ,
            'enums' : enums_ts ,
            'index' : index_ts ,
        }

        for filename , content in files_content.items() :
            filepath = os.path.join(self.output_dir , f'{filename}.ts')
            with open(filepath , 'w' , encoding='utf-8') as f :
                f.write(content)

        print(f"✅ TypeScript интерфейсы сгенерированы в: {self.output_dir}")
        return files_content

    def _generate_models_ts(self , models: List[Model]) -> str :
        """Генерирует TypeScript интерфейсы для моделей"""
        lines = [
            "// ===========================================" ,
            "// AUTOGENERATED TYPESCRIPT INTERFACES" ,
            "// DO NOT EDIT MANUALLY" ,
            "// Generated from Django models" ,
            "// ===========================================" ,
            "" ,
            "/* eslint-disable */" ,
            "// @ts-nocheck" ,
            "" ,
        ]

        # Сначала генерируем базовые интерфейсы
        lines.extend(self._get_base_interfaces())
        lines.append("")

        # Затем генерируем интерфейсы для каждой модели
        for model in models :
            interface_lines = self._generate_model_interface(model)
            if interface_lines :
                lines.extend(interface_lines)
                lines.append("")

        return "\n".join(lines)

    def _get_base_interfaces(self) -> List[str] :
        """Базовые интерфейсы для системы"""
        return [
            "// Base field interface" ,
            "export interface IBaseField {" ,
            "  name: string;" ,
            "  label: string;" ,
            "  value: any;" ,
            "  formatted_value: string;" ,
            "  type: string;" ,
            "  is_empty: boolean;" ,
            "}" ,
            "" ,
            "// Display field interface" ,
            "export interface IDisplayField extends IBaseField {" ,
            "  icon?: string;" ,
            "  priority?: number;" ,
            "  css_class?: string;" ,
            "  metadata?: Record<string, any>;" ,
            "}" ,
            "" ,
            "// Display data structure" ,
            "export interface IDisplayData {" ,
            "  fields: Record<string, IDisplayField>;" ,
            "  view_type?: 'list' | 'card' | 'detail' | 'badge' | 'inline';" ,
            "  timestamp?: string;" ,
            "  model_name?: string;" ,
            "  model_app?: string;" ,
            "}" ,
            "" ,
            "// Compact data structure" ,
            "export interface ICompactData {" ,
            "  id: number;" ,
            "  name?: string;" ,
            "  code?: string;" ,
            "  is_active: boolean;" ,
            "  model: string;" ,
            "  app: string;" ,
            "  [key: string]: any;" ,
            "}" ,
            "" ,
            "// Full data structure" ,
            "export interface IFullData {" ,
            "  compact?: ICompactData;" ,
            "  display?: IDisplayData;" ,
            "  form?: Record<string, any>;" ,
            "  metadata?: Record<string, any>;" ,
            "  related?: Record<string, any>;" ,
            "}" ,
        ]

    def _generate_model_interface(self , model: Model) -> List[str] :
        """Генерирует TypeScript интерфейс для одной модели"""
        model_name = model.__name__
        interface_name = f"I{model_name}"

        if interface_name in self.generated_interfaces :
            return []

        self.generated_interfaces.add(interface_name)

        lines = [
            f"// {model._meta.verbose_name or model_name}" ,
            f"// App: {model._meta.app_label}" ,
            f"export interface {interface_name} {{" ,
        ]

        # Базовые поля
        base_fields = self._get_base_fields()
        for field_name , field_type in base_fields.items() :
            if field_name == '_str' :
                lines.append(f"  toString(): string;  // __str__ method")
            else :
                lines.append(f"  {field_name}: {field_type};")

        # Поля модели
        for field in model._meta.fields :
            # Пропускаем уже добавленные базовые поля
            if field.name in ['id' , 'created_at' , 'updated_at'] :
                continue

            field_info = self._get_field_info(field)
            lines.append(f"  {field.name}{field_info['optional']}: {field_info['type']};")

        # ManyToMany поля
        for field in model._meta.many_to_many :
            field_info = self._get_field_info(field)
            lines.append(f"  {field.name}{field_info['optional']}: {field_info['type']};")

        # Методы get_*_data если есть
        if hasattr(model , 'get_compact_data') :
            lines.append("  compact_data?: ICompactData;")

        if hasattr(model , 'get_display_data') :
            lines.append("  display_data?: IDisplayData;")

        if hasattr(model , 'get_full_data') :
            lines.append("  full_data?: IFullData;")

        lines.append("}")

        # Генерируем дополнительные типы если нужно
        additional_types = self._generate_additional_types(model)
        if additional_types :
            lines.append("")
            lines.extend(additional_types)

        return lines

    def _generate_additional_types(self , model: Model) -> List[str] :
        """Генерирует дополнительные типы для модели"""
        types = []
        model_name = model.__name__

        # Тип для формы
        form_interface = f"I{model_name}Form"
        types.extend([
            f"export interface {form_interface} {{" ,
        ])

        # Добавляем только редактируемые поля
        for field in model._meta.fields :
            if field.name in ['id' , 'created_at' , 'updated_at'] :
                continue

            field_info = self._get_field_info(field)
            # Для формы все поля optional
            types.append(f"  {field.name}?: {field_info['raw_type'].replace(' | null' , '')};")

        types.append("}")

        return types

    def _generate_enums_ts(self , models: List[Model]) -> str :
        """Генерирует TypeScript перечисления"""
        lines = [
            "// ===========================================" ,
            "// AUTOGENERATED ENUMS" ,
            "// DO NOT EDIT MANUALLY" ,
            "// ===========================================" ,
            "" ,
            "/* eslint-disable */" ,
            "// @ts-nocheck" ,
            "" ,
        ]

        enums = self._collect_enums(models)

        for enum_name , values in enums.items() :
            if not values :
                continue

            lines.append(f"export enum {enum_name} {{")

            for key , value in values :
                # Обработка ключей для TypeScript
                ts_key = self._format_enum_key(key)

                if isinstance(value , str) :
                    lines.append(f'  {ts_key} = "{value}",')
                elif isinstance(value , (int , float)) :
                    lines.append(f"  {ts_key} = {value},")
                else :
                    lines.append(f'  {ts_key} = "{str(value)}",')

            lines.append("}")
            lines.append("")

        # Общие типы
        lines.extend([
            "// Common types" ,
            "export type ViewType = 'list' | 'card' | 'detail' | 'badge' | 'inline';" ,
            "export type DataFormat = 'compact' | 'display' | 'full' | 'export';" ,
            "export type FieldType = 'text' | 'textarea' | 'number' | 'date' | 'datetime' | 'boolean' | 'select' | 'multiselect' | 'url' | 'email' | 'file' | 'image';" ,
            "" ,
            "// Status types" ,
            "export type StatusType = 'draft' | 'published' | 'archived' | 'deleted';" ,
            "export type ActiveStatus = 'active' | 'inactive' | 'pending';" ,
        ])

        return "\n".join(lines)

    def _format_enum_key(self , key: str) -> str :
        """Форматирует ключ enum для TypeScript"""
        # Убираем специальные символы, заменяем пробелы на подчеркивания
        key = str(key).strip().upper()
        key = key.replace(' ' , '_')
        key = key.replace('-' , '_')
        key = key.replace('.' , '_')
        key = ''.join(c for c in key if c.isalnum() or c == '_')

        # Если ключ начинается с цифры, добавляем префикс
        if key and key[0].isdigit() :
            key = 'VALUE_' + key

        return key

    def _collect_enums(self , models: List[Model]) -> Dict[str , List[tuple]] :
        """Собирает все перечисления из моделей"""
        enums = {}

        for model in models :
            # Ищем поля с choices
            for field in model._meta.fields :
                if hasattr(field , 'choices') and field.choices :
                    # Создаем имя для enum
                    model_name = model.__name__
                    field_name = field.name.replace('_' , ' ').title().replace(' ' , '')
                    enum_name = f"E{model_name}{field_name}"

                    enums[enum_name] = field.choices

            # Ищем атрибуты CHOICES_ в классе модели
            for attr_name in dir(model) :
                if attr_name.startswith('CHOICES_') :
                    attr_value = getattr(model , attr_name)
                    if isinstance(attr_value , (list , tuple)) :
                        enum_suffix = attr_name[8 :].replace('_' , ' ').title().replace(' ' , '')
                        enum_name = f"E{model.__name__}{enum_suffix}"
                        enums[enum_name] = attr_value

        return enums

    def _generate_index_ts(self) -> str :
        """Генерирует index.ts файл для экспорта всех типов"""
        lines = [
            "// ===========================================" ,
            "// AUTOEXPORT ALL GENERATED TYPES" ,
            "// DO NOT EDIT MANUALLY" ,
            "// ===========================================" ,
            "" ,
            "/* eslint-disable */" ,
            "// @ts-nocheck" ,
            "" ,
            "// Export all interfaces and enums" ,
            "export * from './models';" ,
            "export * from './enums';" ,
            "" ,
            "// Common re-exports" ,
            "export type {" ,
            "  IBaseField," ,
            "  IDisplayField," ,
            "  IDisplayData," ,
            "  ICompactData," ,
            "  IFullData," ,
            "  ViewType," ,
            "  DataFormat," ,
            "  FieldType," ,
            "  StatusType," ,
            "  ActiveStatus," ,
            "} from './models';" ,
            "" ,
            "// Utility types" ,
            "export type Nullable<T> = T | null;" ,
            "export type Optional<T> = T | undefined;" ,
            "export type WithId<T> = T & { id: number };" ,
            "export type Dictionary<T> = Record<string, T>;" ,
            "" ,
            "// API Response types" ,
            "export interface ApiResponse<T = any> {" ,
            "  data: T;" ,
            "  success: boolean;" ,
            "  message?: string;" ,
            "  errors?: Record<string, string[]>;" ,
            "  metadata?: {" ,
            "    count?: number;" ,
            "    total?: number;" ,
            "    page?: number;" ,
            "    page_size?: number;" ,
            "    total_pages?: number;" ,
            "    current_page?: number;" ,
            "  };" ,
            "}" ,
            "" ,
            "// Pagination types" ,
            "export interface PaginationParams {" ,
            "  page?: number;" ,
            "  page_size?: number;" ,
            "  ordering?: string;" ,
            "  search?: string;" ,
            "  filters?: Record<string, any>;" ,
            "}" ,
            "" ,
            "export interface PaginatedResponse<T> {" ,
            "  results: T[];" ,
            "  count: number;" ,
            "  total_pages: number;" ,
            "  current_page: number;" ,
            "  page_size: number;" ,
            "  next?: string | null;" ,
            "  previous?: string | null;" ,
            "}" ,
        ]

        return "\n".join(lines)


def generate_typescript_interfaces(output_dir: str = None , include_apps: List[str] = None) -> Dict[str , str] :
    """
    Основная функция для генерации TypeScript интерфейсов.

    Args:
        output_dir: Директория для сохранения
        include_apps: Список приложений для обработки

    Returns:
        Dict с путями файлов и их содержимым
    """
    generator = TypeScriptGenerator(output_dir , include_apps)
    return generator.generate_all()