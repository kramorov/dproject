from django.core.exceptions import ValidationError

from valve_data.models.mixins import ValveLineDataGettersMixin


class ValveLineServiceMixin(ValveLineDataGettersMixin):
    """Миксин для сервисных методов"""

    def get_service_life_info(self, show_data_source=False):
        """Получает информацию о сроках службы с учетом наследования"""
        warranty_min = self.effective_warranty_period_min
        warranty_min_variety = self.effective_warranty_period_min_variety
        warranty_max = self.effective_warranty_period_max
        warranty_max_variety = self.effective_warranty_period_max_variety
        service_years = self.effective_valve_in_service_years
        service_years_comment = self.effective_valve_in_service_years_comment
        service_cycles = self.effective_valve_in_service_cycles
        service_cycles_comment = self.effective_valve_in_service_cycles_comment

        result = []

        # Гарантийные сроки - проверяем только на None
        if warranty_min is not None:
            min_text = f"{warranty_min} мес."
            if warranty_min_variety not in [None, '']:
                min_text += f" ({warranty_min_variety})"
            result.append({
                'label': 'Гарантийный срок мин',
                'value': min_text
            })

        if warranty_max is not None:
            max_text = f"{warranty_max} мес."
            if warranty_max_variety not in [None, '']:
                max_text += f" ({warranty_max_variety})"
            result.append({
                'label': 'Гарантийный срок макс',
                'value': max_text
            })

        # Срок эксплуатации
        if service_years is not None:
            years_text = f"{service_years} лет"
            if service_years_comment not in [None, '']:
                years_text += f" ({service_years_comment})"
            result.append({
                'label': 'Срок эксплуатации',
                'value': years_text
            })

        # Количество циклов
        if service_cycles is not None:
            cycles_text = f"{service_cycles} циклов"
            if service_cycles_comment not in [None, '']:
                cycles_text += f" ({service_cycles_comment})"
            result.append({
                'label': 'Количество циклов',
                'value': cycles_text
            })

        return result

    def get_status_info(self, show_data_source=False):
        """Получает информацию о статусах"""
        return {
            'active': "Активна" if self.is_active else "Не активна",
            'approved': "Проверена" if self.is_approved else "Не проверена",
        }

    def get_validation_warnings(self):
        """Возвращает предупреждения о потенциальных проблемах"""
        warnings = []

        # Проверка обязательных полей
        missing_fields = self.get_missing_required_fields()
        if missing_fields:
            warnings.append(f"Обязательные поля не заполнены и не будут унаследованы: {', '.join(missing_fields)}")

        # Проверка глубины наследования
        if self.original_valve_line:
            depth = self._get_inheritance_depth()
            if depth > 3:
                warnings.append(f"Глубокая цепочка наследования ({depth} уровней), что может замедлить работу")

        # Проверка на одинаковые названия в цепочке наследования
        if self.name and self.original_valve_line:
            current = self.original_valve_line
            while current:
                if current.name == self.name:
                    warnings.append("Название совпадает с одним из родителей в цепочке наследования")
                    break
                current = current.original_valve_line

        return warnings

    def clean(self):
        """Валидация модели перед сохранением"""
        from django.core.exceptions import ValidationError

        errors = {}

        # Проверка обязательных полей
        if not self.name and not self.original_valve_line:
            errors['name'] = 'Название серии обязательно, если не указана исходная серия'

        if not self.code and not self.original_valve_line:
            errors['code'] = 'Код серии обязателен, если не указана исходная серия'

        if not self.valve_brand and not self.original_valve_line:
            errors['valve_brand'] = 'Бренд обязателен, если не указана исходная серия'

        if not self.valve_producer and not self.original_valve_line:
            errors['valve_producer'] = 'Производитель обязателен, если не указана исходная серия'

        # Проверка циклических ссылок
        if self.original_valve_line and self.original_valve_line == self:
            errors['original_valve_line'] = 'Нельзя указывать текущую серию как исходную'

        # Проверка глубины наследования
        if self.original_valve_line:
            depth = self._get_inheritance_depth()
            if depth > 5:
                errors[
                    'original_valve_line'] = f'Слишком глубокая цепочка наследования ({depth} уровней). Максимум 5 уровней.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Переопределяем save для автоматической проверки"""
        self.full_clean()
        super().save(*args, **kwargs)