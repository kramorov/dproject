# pneumatic_fittings/catalog/views_common.py
"""
Общее для трёх каталогов фитингов.

KindFilterOptionsMixin — реализация get() для фильтр-вьюх, в которой опции
считаются в пределах вида каталога (KindCatalogConfig.get_scoped_queryset),
а не по всей модели PneumaticFitting.
"""
from rest_framework.response import Response


class KindFilterOptionsMixin:
    """Опции фильтров считаются по queryset, суженному до вида каталога."""

    def get(self, request):
        scope = request.query_params.get('scope', getattr(self, 'default_scope', 'list'))
        config = self.catalog_config
        filter_set = config.get_filter_set(scope)
        model_line_id = request.query_params.get('model_line_id')
        base_qs = config.get_scoped_queryset(model_line_id)

        result = {}
        for fd in filter_set.definitions:
            try:
                options = fd.get_options(config.model_class, queryset=base_qs)
                # CUSTOM фильтры могут возвращать пустой список —
                # всё равно включаем, чтобы фронт нарисовал спец-компонент
                is_custom = fd.data_source_type.value == 'custom'
                if options or is_custom:
                    result[fd.param_name] = {
                        'label': fd.label,
                        'order': fd.order,
                        'filter_type': fd.filter_type.value,
                        'options': options,
                        'default_value': fd.default_value,
                        'show_code': fd.show_code,
                    }
            except Exception as e:
                result[fd.param_name] = {
                    'label': fd.label,
                    'order': fd.order,
                    'options': [],
                    'error': str(e),
                }

        return Response({
            'filters': result,
            'show_compatible': filter_set.show_compatible,
        })
