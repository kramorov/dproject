# electric_actuators/utils/universal_renderer.py
from jinja2 import Environment , FileSystemLoader , Template
from docxtpl import DocxTemplate
from pathlib import Path
import io
import logging
from datetime import datetime
from django.http import HttpResponse , JsonResponse

logger = logging.getLogger(__name__)


class UniversalTemplateRenderer :
    """
    Универсальный рендерер для HTML и Word документов.
    Использует один Jinja2 шаблон для всех форматов.
    """

    def __init__(self , template_dir=None) :
        """Инициализация"""
        if template_dir is None :
            self.template_dir = Path(__file__).parent.parent / 'templates' / 'electric_actuators'
        else :
            self.template_dir = Path(template_dir)

        # Настройка Jinja2 для HTML
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir) ,
            trim_blocks=True ,
            lstrip_blocks=True ,
            autoescape=False
        )

        # Регистрируем пользовательские фильтры
        self._register_filters()

    def _register_filters(self) :
        """Регистрирует пользовательские фильтры Jinja2"""

        def format_currency(value , currency='₽') :
            """Форматирует валюту"""
            try :
                return f"{float(value):,.2f} {currency}".replace(',' , ' ')
            except :
                return value

        def default_if_none(value , default='—') :
            """Заменяет None на значение по умолчанию"""
            return value if value is not None else default

        def format_bool(value , true_text='Да' , false_text='Нет') :
            """Форматирует булево значение"""
            return true_text if value else false_text

        self.jinja_env.filters['currency'] = format_currency
        self.jinja_env.filters['default'] = default_if_none
        self.jinja_env.filters['bool'] = format_bool

    def prepare_data(self , raw_data) :
        """
        Подготавливает данные из _generate_short_description для шаблона

        Args:
            raw_data: словарь из _generate_short_description()

        Returns:
            dict: подготовленные данные для шаблона
        """
        prepared = {
            'model' : raw_data.get('model' , {}) ,
            'code' : raw_data.get('model' , {}).get('name') ,
            'brand' : raw_data.get('brand' , {}) ,
            'generated_at' : datetime.now().strftime('%d.%m.%Y %H:%M') ,
            'basic_params' : [] ,
            'electrical_params' : [] ,
            'mechanical_params' : [] ,
        }

        # Определяем категории параметров
        electrical_keys = ['power_supply' , 'motor_current_rated' , 'motor_current_starting' , 'motor_power']
        mechanical_keys = ['time_to_open' , 'time_to_close' , 'torque_min' , 'torque_max' ,
                           'mounting_plate' , 'stem_shape' , 'stem_size' , 'cable_glands_holes']

        # Единицы измерения
        units = {
            'power_supply' : 'В' ,
            'motor_current_rated' : 'А' ,
            'motor_current_starting' : 'А' ,
            'motor_power' : 'кВт' ,
            'time_to_open' : 'с' ,
            'time_to_close' : 'с' ,
            'torque_min' : 'Нм' ,
            'torque_max' : 'Нм' ,
        }

        # Обрабатываем все ключи из raw_data
        for key , value in raw_data.items() :
            if key == 'model' or key == 'brand' or key == 'code' :
                continue

            # Добавляем единицу измерения если есть
            if isinstance(value , dict) :
                value_copy = value.copy()
                if key in units :
                    value_copy['unit'] = units[key]
                else :
                    value_copy['unit'] = None

                # Категоризируем
                if key in electrical_keys :
                    prepared['electrical_params'].append(value_copy)
                elif key in mechanical_keys :
                    prepared['mechanical_params'].append(value_copy)
                elif key.startswith('selected_') or key.endswith('_data') :
                    # Это составные опции, сохраняем как есть для детального вывода
                    prepared[key] = value_copy
                else :
                    prepared['basic_params'].append(value_copy)

        # Сортируем параметры по display_name
        for param_list in ['basic_params' , 'electrical_params' , 'mechanical_params'] :
            prepared[param_list].sort(key=lambda x : x.get('display_name' , ''))

        return prepared

    def render_html(self , template_name , data) :
        """
        Рендерит HTML из шаблона

        Args:
            template_name: имя файла шаблона
            data: подготовленные данные

        Returns:
            str: HTML строка
        """
        template = self.jinja_env.get_template(template_name)
        return template.render(**data)

    def render_docx(self , template_name , data) :
        """
        Рендерит Word документ из того же шаблона

        Args:
            template_name: имя файла шаблона
            data: подготовленные данные

        Returns:
            bytes: бинарные данные Word документа
        """
        # Для Word используем docxtpl
        template_path = self.template_dir / template_name

        # Конвертируем .j2 в .docx если нужно
        docx_template_path = template_path.with_suffix('.docx')

        # Если нет .docx версии, создаем её из .j2
        if not docx_template_path.exists() :
            self._create_docx_template(template_path , docx_template_path)

        doc = DocxTemplate(str(docx_template_path))

        # docxtpl требует специфической обработки для таблиц
        # Преобразуем данные в нужный формат
        docx_data = self._prepare_for_docx(data)

        doc.render(docx_data)

        output = io.BytesIO()
        doc.save(output)
        output.seek(0)

        return output.getvalue()

    def _create_docx_template(self , jinja_path , docx_path) :
        """Создает Word шаблон из Jinja2 шаблона"""
        # Здесь можно создать базовый .docx с текстом из .j2
        # Или просто скопировать .j2 в .docx с конвертацией
        import docx

        doc = docx.Document()

        # Читаем Jinja2 шаблон
        with open(jinja_path , 'r' , encoding='utf-8') as f :
            content = f.read()

        # Добавляем содержимое как текст (в упрощенном виде)
        # В реальном проекте вы захотите создать нормальный Word шаблон вручную
        for line in content.split('\n') :
            if line.strip() :
                doc.add_paragraph(line)

        doc.save(docx_path)

    def _prepare_for_docx(self , data) :
        """Подготавливает данные для docxtpl"""

        # docxtpl требует, чтобы все вложенные словари были преобразованы
        # в простые структуры

        def flatten_dict(d , parent_key='' , sep='_') :
            """Преобразует вложенные словари в плоские ключи"""
            items = []
            for k , v in d.items() :
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v , dict) :
                    items.extend(flatten_dict(v , new_key , sep=sep).items())
                else :
                    items.append((new_key , v))
            return dict(items)

        # Для таблиц docxtpl нужны списки словарей
        result = {}

        for key , value in data.items() :
            if key in ['basic_params' , 'electrical_params' , 'mechanical_params'] :
                # Для таблиц преобразуем в список словарей
                result[key] = value
            elif isinstance(value , dict) :
                # Для сложных опций делаем плоские ключи
                flat = flatten_dict({key : value})
                result.update(flat)
            else :
                result[key] = value

        return result

    def response_html(self , request , instance_id) :
        """HTTP ответ с HTML"""
        from electric_actuators.models.ea_actuator_selected import ElectricActuatorSelected

        instance = ElectricActuatorSelected.objects.get(id=instance_id)
        raw_data = instance._generate_short_description()
        data = self.prepare_data(raw_data)

        html = self.render_html('description_template.j2' , data)

        return HttpResponse(html)

    def response_json_html(self , request , instance_id) :
        """JSON ответ с HTML для AJAX"""
        from electric_actuators.models.ea_actuator_selected import ElectricActuatorSelected

        instance = ElectricActuatorSelected.objects.get(id=instance_id)
        raw_data = instance._generate_short_description()
        data = self.prepare_data(raw_data)

        html = self.render_html('description_template.j2' , data)

        return JsonResponse({
            'success' : True ,
            'html' : html ,
            'data' : data
        })

    def response_docx(self , request , instance_id) :
        """HTTP ответ с Word документом"""
        from electric_actuators.models.ea_actuator_selected import ElectricActuatorSelected

        instance = ElectricActuatorSelected.objects.get(id=instance_id)
        raw_data = instance._generate_short_description()
        data = self.prepare_data(raw_data)

        docx_bytes = self.render_docx('description_template.j2' , data)

        response = HttpResponse(
            docx_bytes ,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="description_{instance_id}.docx"'

        return response