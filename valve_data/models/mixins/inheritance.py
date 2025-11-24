from django.core.exceptions import ValidationError


class ValveLineInheritanceMixin:
    """Миксин для работы с наследованием"""

    def get_field_value_with_fallback(self, field_name, show_data_source=False, recursion_level=0, max_recursion=5):
        """
        Рекурсивно получает значение поля с учетом original_valve_line
        """
        if recursion_level >= max_recursion:
            if show_data_source:
                return {
                    'value': None,
                    'source': None,
                    'comment': f"Достигнут максимальный уровень рекурсии ({max_recursion})"
                }
            return None

        # Получаем значение из текущей модели
        current_value = getattr(self, field_name, None)

        # Проверяем, является ли значение "пустым"
        is_empty = self._is_value_empty(current_value)

        # Если значение есть и оно не пустое, возвращаем его
        if not is_empty:
            if show_data_source:
                return {
                    'value': current_value,
                    'source': self,
                    'comment': f"Значение из модели: {self.name}"
                }
            else:
                return current_value

        # Если значения нет, проверяем original_valve_line
        if self.original_valve_line:
            fallback_result = self.original_valve_line.get_field_value_with_fallback(
                field_name, show_data_source, recursion_level + 1, max_recursion
            )

            if fallback_result:
                if show_data_source:
                    if isinstance(fallback_result, dict) and fallback_result.get('value') is not None:
                        fallback_result[
                            'comment'] = f"Значение унаследовано из: {self.original_valve_line.name} (уровень {recursion_level + 1})"
                    return fallback_result
                else:
                    return fallback_result

        # Если ничего не найдено
        if show_data_source:
            return {
                'value': None,
                'source': None,
                'comment': "Значение не найдено"
            }
        return None

    def _is_value_empty(self, value):
        """Проверяет, является ли значение пустым"""
        if value is None:
            return True
        elif isinstance(value, str) and value.strip() == '':
            return True
        elif hasattr(value, 'pk') and not value.pk:
            return True
        return False

    def _get_inheritance_depth(self, current_level=0, max_level=10):
        """Рекурсивно вычисляет глубину цепочки наследования"""
        if current_level >= max_level:
            return current_level

        if self.original_valve_line:
            return self.original_valve_line._get_inheritance_depth(current_level + 1, max_level)

        return current_level

    def _will_inherit(self, field_name):
        """Проверяет, будет ли поле унаследовано от original_valve_line"""
        if not self.original_valve_line:
            return False

        # Проверяем, есть ли значение в цепочке наследования
        current = self.original_valve_line
        visited = set()
        depth = 0

        while current and depth < 10:
            if current.id in visited:
                break
            visited.add(current.id)

            value = getattr(current, field_name, None)
            if value not in [None, '']:
                return True

            if not current.original_valve_line:
                break

            current = current.original_valve_line
            depth += 1

        return False

    def get_missing_required_fields(self):
        """Возвращает список обязательных полей, которые не заполнены и не наследуются"""
        missing_fields = []

        if not self.name and not self._will_inherit('name'):
            missing_fields.append('name')

        if not self.code and not self._will_inherit('code'):
            missing_fields.append('code')

        if not self.valve_brand and not self._will_inherit('valve_brand'):
            missing_fields.append('valve_brand')

        if not self.valve_producer and not self._will_inherit('valve_producer'):
            missing_fields.append('valve_producer')

        return missing_fields