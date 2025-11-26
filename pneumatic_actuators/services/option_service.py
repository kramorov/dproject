from typing import Dict , List , Optional
from django.db import models



class OptionService :
    """Сервис для работы с опциями пневмоприводов"""

    @staticmethod
    def get_available_options(model_id: int) -> Dict[str , List[Dict]] :
        """Получить все доступные опции для модели"""
        # from .models import (
        #     PneumaticActuatorModelLineItem ,
        #     PneumaticSafetyPositionOption ,
        #     PneumaticSpringsQtyOption
        # )
        from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLineItem
        from pneumatic_actuators.models.pa_options import PneumaticSafetyPositionOption, PneumaticSpringsQtyOption
        from pneumatic_actuators.models.pa_options import PneumaticTemperatureOption , PneumaticIpOption, PneumaticExdOption , PneumaticBodyCoatingOption
        try :
            model = PneumaticActuatorModelLineItem.objects.get(id=model_id)

            # Существующие опции
            safety_options = PneumaticSafetyPositionOption.objects.filter(
                model_line_item=model ,
                is_active=True
            ).select_related('safety_position')

            springs_options = PneumaticSpringsQtyOption.objects.filter(
                model_line_item=model ,
                is_active=True
            ).select_related('springs_qty')

            # НОВЫЕ ОПЦИИ через model_line
            temperature_options = []
            ip_options = []
            exd_options = []
            body_coating_options = []

            if model.model_line :
                temperature_options = PneumaticTemperatureOption.objects.filter(
                    model_line=model.model_line ,
                    is_active=True
                )

                ip_options = PneumaticIpOption.objects.filter(
                    model_line=model.model_line ,
                    is_active=True
                )

                exd_options = PneumaticExdOption.objects.filter(
                    model_line=model.model_line ,
                    is_active=True
                )

                body_coating_options = PneumaticBodyCoatingOption.objects.filter(
                    model_line=model.model_line ,
                    is_active=True
                )

            return {
                'safety_positions' : [
                    {
                        'id' : opt.id ,
                        'encoding' : opt.encoding ,
                        'name' : opt.safety_position.name ,
                        'description' : opt.description ,
                        'is_default' : opt.is_default
                    } for opt in safety_options
                ] ,
                'springs_qty' : [
                    {
                        'id' : opt.id ,
                        'encoding' : opt.encoding ,
                        'name' : opt.springs_qty.name ,
                        'description' : opt.description ,
                        'is_default' : opt.is_default
                    } for opt in springs_options
                ] ,
                # НОВЫЕ ОПЦИИ
                'temperature_options' : [
                    {
                        'id' : opt.id ,
                        'encoding' : opt.encoding ,
                        'name': str(opt),  # используем __str__ метод
                        'description' : opt.description ,
                        'is_default' : opt.is_default
                    } for opt in temperature_options
                ] ,
                'ip_options' : [
                    {
                        'id' : opt.id ,
                        'encoding' : opt.encoding ,
                        'name': str(opt),  # используем __str__ метод
                        'description' : opt.description ,
                        'is_default' : opt.is_default
                    } for opt in ip_options
                ] ,
                'exd_options' : [
                    {
                        'id' : opt.id ,
                        'encoding' : opt.encoding ,
                        'name': str(opt),  # используем __str__ метод
                        'description' : opt.description ,
                        'is_default' : opt.is_default
                    } for opt in exd_options
                ] ,
                'body_coating_options' : [
                    {
                        'id' : opt.id ,
                        'encoding' : opt.encoding ,
                        'name': str(opt),  # используем __str__ метод
                        'description' : opt.description ,
                        'is_default' : opt.is_default
                    } for opt in body_coating_options
                ]
            }
        except PneumaticActuatorModelLineItem.DoesNotExist :
            return {
                'safety_positions' : [] , 'springs_qty' : [] ,
                'temperature_options' : [] , 'ip_options' : [] ,
                'exd_options' : [] , 'body_coating_options' : []
            }

    @staticmethod
    def generate_actuator_data(model_id: int , safety_option_id: int = None , springs_option_id: int = None) -> Dict :
        """Сгенерировать данные для привода (название, код, описание)"""
        from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLineItem
        from pneumatic_actuators.models.pa_options import PneumaticSafetyPositionOption , PneumaticSpringsQtyOption

        model = PneumaticActuatorModelLineItem.objects.get(id=model_id)
        safety_option = None
        springs_option = None

        if safety_option_id :
            safety_option = PneumaticSafetyPositionOption.objects.get(id=safety_option_id)
        if springs_option_id :
            springs_option = PneumaticSpringsQtyOption.objects.get(id=springs_option_id)

        # Используем твои существующие методы генерации
        # или выносим их тоже в сервис
        name = OptionService._generate_name(model , safety_option , springs_option)
        code = OptionService._generate_code(model , safety_option , springs_option)
        description = OptionService._generate_description(model , safety_option , springs_option)

        return {
            'name' : name ,
            'code' : code ,
            'description' : description
        }

    @staticmethod
    def _generate_name(model , safety_option , springs_option) -> str :
        # Выносим логику из модели в сервис
        name_parts = [model.name]
        if safety_option :
            name_parts.append(str(safety_option.safety_position))
        if springs_option :
            name_parts.append(str(springs_option.springs_qty))
        return " - ".join(name_parts)

    def _generate_code(model , safety_option , springs_option) -> str :
        """Сгенерировать код привода"""

        code_parts = [model.code or model.name[:10]]

        if safety_option and safety_option.encoding :
            code_parts.append(safety_option.encoding)

        if springs_option and springs_option.encoding :
            code_parts.append(springs_option.encoding)

        return "-".join(code_parts)

    def _generate_description(model , safety_option , springs_option) -> str :
        """Сгенерировать описание привода"""
        desc_parts = [f"Модель: {model.name}"]

        if safety_option :
            desc_parts.append(f"Положение безопасности: {safety_option.safety_position.name}")
            if safety_option.description :
                desc_parts.append(f"Описание: {safety_option.description}")

        if springs_option :
            desc_parts.append(f"Количество пружин: {springs_option.springs_qty.name}")
            if springs_option.description :
                desc_parts.append(f"Описание: {springs_option.description}")

        return "\n".join(desc_parts)
