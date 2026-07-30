# core/wizard_views.py
"""
API endpoints для мастера подбора (Selection Wizard).

Публичные (каталог):
  GET  /api/core/wizard/<equipment_type_id>/          — конфигурация мастера
  POST /api/core/wizard/<equipment_type_id>/filter-options/ — опции фильтра с description
  POST /api/core/wizard/<equipment_type_id>/results/  — подбор с пагинацией
  GET  /api/core/wizard/model-filters/                — FILTER_DEFINITIONS по content_type_id

Админские (CRUD):
  GET    /api/core/wizard/admin/           — список всех мастеров
  POST   /api/core/wizard/admin/           — создать мастера
  GET    /api/core/wizard/admin/<id>/      — получить одного
  PUT    /api/core/wizard/admin/<id>/      — обновить
  DELETE /api/core/wizard/admin/<id>/      — удалить
"""
import logging
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, BasePermission

from core.access import catalog_permission_classes
from core.models.equipment_type import EquipmentType
from core.models.selection_wizard import SelectionWizard
from core.models.filter_definition import FilterType, DataSourceType
from core.wizard_filter_registry import get_filter_definitions_for_ct

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Permissions
# ═══════════════════════════════════════════════════════════════════════

class IsAdminOrSuperuser(BasePermission):
    """
    Разрешает доступ суперпользователям Django.
    В текущей архитектуре CurrentUserView возвращает roles=['admin']
    только для is_superuser. Для кастомных ролей проверка через сессию.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_superuser or user.is_staff


# ═══════════════════════════════════════════════════════════════════════
# Mixin: общие методы для работы с EquipmentType и FilterDefinition
# ═══════════════════════════════════════════════════════════════════════

class WizardModelMixin:
    """Методы, общие для всех wizard-views: получение модели и FilterDefinition."""

    def _get_model_class(self, et: EquipmentType):
        """Получить класс модели Django из EquipmentType.content_type."""
        ct = et.content_type
        if not ct:
            return None
        try:
            return ct.model_class()
        except Exception:
            return None

    def _find_filter_definition(self, model_class, param_name: str):
        """Найти FilterDefinition — сначала в модели, затем в реестре."""
        # 1. Search model's own FILTER_DEFINITIONS
        if hasattr(model_class, 'FILTER_DEFINITIONS'):
            for fd in model_class.FILTER_DEFINITIONS:
                if fd.param_name == param_name:
                    return fd
        # 2. Fallback: search registry (model may have additional FDs
        #    in catalog/filter_defs.py not listed on the class)
        registry_defs = self._get_definitions_from_registry(model_class)
        if registry_defs:
            for fd in registry_defs:
                if fd.param_name == param_name:
                    return fd
        return None

    def _get_definitions_from_registry(self, model_class):
        """Попытаться получить filter_definitions через реестр."""
        from django.contrib.contenttypes.models import ContentType
        try:
            ct = ContentType.objects.get_for_model(model_class)
            return get_filter_definitions_for_ct(ct.id)
        except Exception:
            return None

    def _get_equipment_type(self, equipment_type_id: int) -> EquipmentType:
        """Получить EquipmentType или вернуть None."""
        try:
            return EquipmentType.objects.get(id=equipment_type_id)
        except EquipmentType.DoesNotExist:
            return None


# ═══════════════════════════════════════════════════════════════════════
# Публичные views (каталог)
# ═══════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class WizardConfigView(WizardModelMixin, APIView):
    """GET /api/core/wizard/<equipment_type_id>/ — вернуть конфигурацию мастера."""
    permission_classes = catalog_permission_classes()

    def get(self, request, equipment_type_id):
        et = self._get_equipment_type(equipment_type_id)
        if not et:
            return Response({'error': 'EquipmentType not found'}, status=404)

        wizard = et.active_selection_wizard
        if not wizard:
            return Response({'error': 'No active wizard for this equipment type'}, status=404)

        steps = wizard.get_steps()
        return Response({
            'wizard_id': wizard.id,
            'wizard_name': wizard.name,
            'equipment_type_id': et.id,
            'equipment_type_name': et.name,
            'steps': steps,
            'total_steps': len(steps),
        })


@method_decorator(csrf_exempt, name='dispatch')
class WizardFilterOptionsView(WizardModelMixin, APIView):
    """
    POST /api/core/wizard/<equipment_type_id>/filter-options/

    Тело: {"param_name": "sensor_variety_id", "filters_applied": {...}}

    Возвращает опции с полем description.
    """
    permission_classes = catalog_permission_classes()

    def post(self, request, equipment_type_id):
        et = self._get_equipment_type(equipment_type_id)
        if not et:
            return Response({'error': 'EquipmentType not found'}, status=404)

        param_name = request.data.get('param_name')
        if not param_name:
            return Response({'error': 'param_name is required'}, status=400)

        model_class = self._get_model_class(et)
        if not model_class:
            return Response({'error': 'Model class not found'}, status=400)

        fd = self._find_filter_definition(model_class, param_name)
        if not fd:
            return Response({'error': f'Filter "{param_name}" not found'}, status=400)

        filters_applied = request.data.get('filters_applied', {})
        options = self._get_scoped_options(fd, model_class, filters_applied)
        enriched = self._enrich_options(fd, model_class, options)

        return Response({
            'param_name': param_name,
            'label': fd.label,
            'filter_type': fd.filter_type.value if fd.filter_type else 'exact',
            'options': enriched,
        })

    def _get_scoped_options(self, fd, model_class, filters_applied):
        """Получить опции, опционально отфильтрованные по уже выбранным значениям."""
        if not filters_applied:
            return fd.get_options(model_class)

        # Строим scoped queryset на основе уже применённых фильтров
        qs = model_class.objects.filter(is_active=True)
        for pn, val in filters_applied.items():
            if val is None or val == '':
                continue
            other_fd = self._find_filter_definition(model_class, pn)
            if not other_fd or other_fd.param_name == fd.param_name:
                continue
            try:
                lookup, converted = other_fd.build_filter_lookup(val)
                if lookup and converted is not None:
                    qs = qs.filter(**{lookup: converted})
            except Exception:
                pass

        return fd.get_options(model_class, queryset=qs)

    def _enrich_options(self, fd, model_class, options):
        """Добавить поле 'description' к каждой опции."""
        ds_type = fd.data_source_type
        if ds_type not in (
            DataSourceType.FOREIGN_KEY,
            DataSourceType.UNIQUE_FIELD_VALUES,
            DataSourceType.GLOBAL_MODEL,
        ):
            for opt in options:
                if 'description' not in opt:
                    opt['description'] = opt.get('name', '')
            return options

        ids = [o.get('id') for o in options if o.get('id') is not None]
        if not ids:
            return options

        try:
            if ds_type == DataSourceType.GLOBAL_MODEL and fd.source_model:
                rel_model = fd.source_model
            else:
                parts = fd.model_field.split('__')
                rel_model = model_class
                for part in parts:
                    field = rel_model._meta.get_field(part)
                    if field.is_relation:
                        rel_model = field.remote_field.model

            objects = rel_model.objects.filter(id__in=ids)
            obj_map = {obj.id: obj for obj in objects}

            for opt in options:
                oid = opt.get('id')
                obj = obj_map.get(oid)
                if obj and hasattr(obj, 'description'):
                    opt['description'] = obj.description or ''
                elif obj:
                    opt['description'] = str(obj)
                else:
                    opt['description'] = opt.get('name', '')
        except Exception as e:
            logger.warning(f'Failed to enrich options: {e}')
            for opt in options:
                if 'description' not in opt:
                    opt['description'] = opt.get('name', '')

        return options


@method_decorator(csrf_exempt, name='dispatch')
class WizardResultsView(WizardModelMixin, APIView):
    """
    POST /api/core/wizard/<equipment_type_id>/results/

    Тело: {"filters_applied": {...}, "page": 1, "page_size": 24}
    """
    permission_classes = catalog_permission_classes()

    def post(self, request, equipment_type_id):
        et = self._get_equipment_type(equipment_type_id)
        if not et:
            return Response({'error': 'EquipmentType not found'}, status=404)

        model_class = self._get_model_class(et)
        if not model_class:
            return Response({'error': 'Model class not found'}, status=400)

        filters_applied = request.data.get('filters_applied', {})
        page = int(request.data.get('page', 1))
        page_size = int(request.data.get('page_size', 24))

        qs = model_class.objects.filter(is_active=True)

        for param_name, value in filters_applied.items():
            if value is None or value == '' or value == 'all':
                continue
            fd = self._find_filter_definition(model_class, param_name)
            if not fd:
                continue
            try:
                lookup, converted = fd.build_filter_lookup(value)
                if lookup and converted is not None:
                    qs = qs.filter(**{lookup: converted})
            except Exception as e:
                logger.warning(f'Filter error {param_name}={value}: {e}')

        if hasattr(model_class, 'SELECT_RELATED_FIELDS'):
            qs = qs.select_related(*model_class.SELECT_RELATED_FIELDS)
        elif hasattr(model_class, 'select_related_fields'):
            qs = qs.select_related(*model_class.select_related_fields)

        total = qs.count()
        offset = (page - 1) * page_size
        items_qs = qs[offset:offset + page_size]

        items = []
        for obj in items_qs:
            try:
                items.append(obj.to_dict())
            except Exception:
                try:
                    items.append({'id': obj.id, 'name': str(obj), 'code': getattr(obj, 'code', '')})
                except Exception:
                    items.append({'id': obj.id, 'name': f'#{obj.id}'})

        return Response({
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': max(1, (total + page_size - 1) // page_size) if total > 0 else 0,
            'filters_applied': filters_applied,
        })


@method_decorator(csrf_exempt, name='dispatch')
class WizardModelFiltersView(APIView):
    """
    GET /api/core/wizard/model-filters/?content_type_id=XX

    Читает FILTER_DEFINITIONS модели для кнопки «Заполнить из модели».
    """
    permission_classes = catalog_permission_classes()

    def get(self, request):
        ct_id = request.query_params.get('content_type_id')
        if not ct_id:
            return Response({'error': 'content_type_id is required'}, status=400)

        try:
            ct = ContentType.objects.get(id=ct_id)
            model_class = ct.model_class()
        except Exception:
            return Response({'error': 'ContentType not found'}, status=404)

        if not model_class:
            return Response({'filters': []})

        # Get definitions: model class first, then registry
        definitions = None
        if hasattr(model_class, 'FILTER_DEFINITIONS'):
            definitions = model_class.FILTER_DEFINITIONS
        if not definitions:
            definitions = get_filter_definitions_for_ct(ct.id) or []

        if not definitions:
            return Response({'filters': []})

        filters = []
        for fd in definitions:
            filters.append({
                'param_name': fd.param_name,
                'label': fd.label,
                'filter_type': fd.filter_type.value if fd.filter_type else 'exact',
                'data_source_type': fd.data_source_type.value if fd.data_source_type else 'field_values',
                'order': fd.order,
                'default_value': fd.default_value,
            })

        return Response({
            'filters': filters,
            'model_name': model_class.__name__,
            'content_type_id': ct.id,
        })


# ═══════════════════════════════════════════════════════════════════════
# Админские views (CRUD)
# ═══════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class WizardAdminListView(APIView):
    """
    GET  /api/core/wizard/admin/     — список всех мастеров
    POST /api/core/wizard/admin/     — создать мастера
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperuser]

    def get(self, request):
        wizards = SelectionWizard.objects.select_related('equipment_type').order_by('sorting_order', 'name')
        data = []
        for w in wizards:
            data.append({
                'id': w.id,
                'name': w.name,
                'code': w.code,
                'equipment_type_id': w.equipment_type_id,
                'equipment_type_name': w.equipment_type.name if w.equipment_type else None,
                'is_active': w.is_active,
                'sorting_order': w.sorting_order,
                'steps_json': w.steps_json,
            })
        return Response({'data': data})

    def post(self, request):
        name = request.data.get('name', '')
        if not name or not name.strip():
            return Response({'error': 'name is required'}, status=400)
        equipment_type_id = request.data.get('equipment_type_id')
        if not equipment_type_id:
            return Response({'error': 'equipment_type_id is required'}, status=400)

        try:
            et = EquipmentType.objects.get(id=equipment_type_id)
        except EquipmentType.DoesNotExist:
            return Response({'error': 'EquipmentType not found'}, status=400)

        try:
            wizard = SelectionWizard.objects.create(
                name=name.strip(),
                code=request.data.get('code') or None,
                description=request.data.get('description', ''),
                equipment_type=et,
                steps_json=request.data.get('steps_json', {}),
                is_active=request.data.get('is_active', True),
                sorting_order=request.data.get('sorting_order', 0),
            )
        except Exception as e:
            logger.warning(f'Failed to create wizard: {e}')
            return Response({'error': f'Ошибка создания: {str(e)}'}, status=400)

        return Response({
            'id': wizard.id,
            'name': wizard.name,
            'code': wizard.code,
            'equipment_type_id': wizard.equipment_type_id,
            'equipment_type_name': et.name,
            'is_active': wizard.is_active,
            'steps_json': wizard.steps_json,
        }, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class WizardAdminDetailView(APIView):
    """
    GET    /api/core/wizard/admin/<id>/  — получить одного
    PUT    /api/core/wizard/admin/<id>/  — обновить
    DELETE /api/core/wizard/admin/<id>/  — удалить
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperuser]

    def _get_wizard(self, wizard_id):
        try:
            return SelectionWizard.objects.select_related('equipment_type').get(id=wizard_id)
        except SelectionWizard.DoesNotExist:
            return None

    def get(self, request, wizard_id):
        w = self._get_wizard(wizard_id)
        if not w:
            return Response({'error': 'Not found'}, status=404)
        return Response({
            'id': w.id,
            'name': w.name,
            'code': w.code,
            'equipment_type_id': w.equipment_type_id,
            'equipment_type_name': w.equipment_type.name if w.equipment_type else None,
            'is_active': w.is_active,
            'sorting_order': w.sorting_order,
            'steps_json': w.steps_json,
        })

    def put(self, request, wizard_id):
        w = self._get_wizard(wizard_id)
        if not w:
            return Response({'error': 'Not found'}, status=404)

        if 'name' in request.data:
            name_val = request.data['name']
            if not name_val or not name_val.strip():
                return Response({'error': 'name cannot be empty'}, status=400)
            w.name = name_val.strip()
        if 'code' in request.data:
            w.code = request.data['code'] or None
        if 'description' in request.data:
            w.description = request.data['description']
        if 'equipment_type_id' in request.data:
            try:
                w.equipment_type = EquipmentType.objects.get(id=request.data['equipment_type_id'])
            except EquipmentType.DoesNotExist:
                return Response({'error': 'EquipmentType not found'}, status=400)
        if 'steps_json' in request.data:
            w.steps_json = request.data['steps_json']
        if 'is_active' in request.data:
            w.is_active = request.data['is_active']
        if 'sorting_order' in request.data:
            w.sorting_order = request.data['sorting_order']

        try:
            w.save()
        except Exception as e:
            logger.warning(f'Failed to update wizard: {e}')
            return Response({'error': f'Ошибка обновления: {str(e)}'}, status=400)
        return Response({
            'id': w.id,
            'name': w.name,
            'code': w.code,
            'equipment_type_id': w.equipment_type_id,
            'equipment_type_name': w.equipment_type.name if w.equipment_type else None,
            'is_active': w.is_active,
            'steps_json': w.steps_json,
        })

    def delete(self, request, wizard_id):
        w = self._get_wizard(wizard_id)
        if not w:
            return Response({'error': 'Not found'}, status=404)
        w.delete()
        return Response({'ok': True})


# ═══════════════════════════════════════════════════════════════════════
# Вспомогательный эндпоинт: список EquipmentType для админки мастера
# ═══════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class WizardEquipmentTypesView(APIView):
    """
    GET /api/core/wizard/model-filters/equipment-types/       — список всех
    GET /api/core/wizard/model-filters/equipment-types/<id>/  — content_type_id одного
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperuser]

    def get(self, request, et_id=None):
        if et_id is not None:
            try:
                et = EquipmentType.objects.get(id=et_id)
                return Response({
                    'id': et.id,
                    'name': et.name,
                    'content_type_id': et.content_type_id,
                })
            except EquipmentType.DoesNotExist:
                return Response({'error': 'Not found'}, status=404)

        ets = EquipmentType.objects.filter(is_active=True).order_by('sorting_order', 'name')
        data = [{
            'id': et.id,
            'name': et.name,
            'code': et.code,
            'content_type_id': et.content_type_id,
        } for et in ets]
        return Response({'data': data})
