"""API views for QuestionGraph — question-based selection wizard with sub-pages."""
from rest_framework.views import APIView
from rest_framework.response import Response
from price.services.currency_converter import get_bulk_prices
from core.utils.catalog_helpers import get_currency_code

from core.models.question_graph import QuestionGraph
from core.models.selection_wizard import SelectionWizard


_CROSS_FIELD_FILTERS = {
    ('thread_id', 'thread_type_id'): 'thread__thread_type_id',
}
_FIELD_LOOKUP = {
    'thread_type_id': 'thread__thread_type_id',
}

def _find_filter_def(model_class, param_name):
    """Find FilterDefinition for a param_name using model's FILTER_DEFINITIONS or registry."""
    if hasattr(model_class, 'FILTER_DEFINITIONS'):
        for fd in model_class.FILTER_DEFINITIONS:
            if fd.param_name == param_name:
                return fd
    # Try wizard registry
    from django.contrib.contenttypes.models import ContentType
    from core.wizard_filter_registry import get_filter_definitions_for_ct
    try:
        ct = ContentType.objects.get_for_model(model_class)
        defs = get_filter_definitions_for_ct(ct.id)
        if defs:
            for fd in defs:
                if fd.param_name == param_name:
                    return fd
    except Exception:
        pass
    return None


def _get_options_for_page_node(graph, node, accumulated):
    """Get options for all params in a page node."""
    opts = {}
    for p in node.get('params', []):
        pn = p.get('param_name')
        if pn:
            o = _get_options_for_param(graph.equipment_type, pn, accumulated)
            if o:
                opts[pn] = o
    # Backward compat: old format param_names
    for pn in node.get('param_names', []):
        if pn not in opts:
            o = _get_options_for_param(graph.equipment_type, pn, accumulated)
            if o:
                opts[pn] = o
    return opts

def _resolve_cross_fk_field(model_class, param_name):
    """Look up cross-FK model_field from FilterDefinition or wizard registry."""
    # Try model's own FILTER_DEFINITIONS
    if hasattr(model_class, 'FILTER_DEFINITIONS'):
        for fd in model_class.FILTER_DEFINITIONS:
            if fd.param_name == param_name and '__' in (fd.model_field or ''):
                return fd.model_field
    # Try wizard filter registry
    try:
        from django.contrib.contenttypes.models import ContentType
        from core.wizard_filter_registry import get_filter_definitions_for_ct
        ct = ContentType.objects.get_for_model(model_class)
        defs = get_filter_definitions_for_ct(ct.id)
        if defs:
            for d in defs:
                if d.param_name == param_name:
                    return d.model_field
    except Exception:
        pass
    return None

def _get_options_for_param(equipment_type, param_name, filters_applied=None):
    """Get available option values for a filter param_name from the model's data."""
    filters_applied = filters_applied or {}
    content_type = equipment_type.content_type
    if not content_type:
        return []

    model_class = content_type.model_class()
    if not model_class:
        return []

    qs = model_class.objects.filter(is_active=True)
    for pn, pv in filters_applied.items():
        if pv is None:
            continue
        fd = _find_filter_def(model_class, pn)
        if fd:
            try:
                lookup, converted = fd.build_filter_lookup(pv)
                if lookup and converted is not None:
                    qs = qs.filter(**{lookup: converted})
            except Exception:
                pass

    # Resolve field lookup: use FilterDefinition model_field for cross-FK params
    fd_model_field = _resolve_cross_fk_field(model_class, param_name)
    if fd_model_field and '__' in fd_model_field:
        field_lookup = fd_model_field
    else:
        field_lookup = _FIELD_LOOKUP.get(param_name, param_name.replace('_id', ''))

    # For dotted lookups (e.g., body__thread), get distinct values from qs
    if '__' in field_lookup:
        ids = qs.values_list(field_lookup, flat=True).distinct()
        ids = sorted(set(v for v in ids if v is not None and v != ''))
        if not ids:
            return []
        # Try to resolve related model for human-readable names
        parts = field_lookup.split('__')
        rel_model = model_class
        for part in parts:
            try:
                f = rel_model._meta.get_field(part)
                if hasattr(f, 'remote_field') and f.remote_field:
                    rel_model = f.remote_field.model
            except Exception:
                rel_model = None
                break
        if rel_model and hasattr(rel_model, 'objects'):
            obj_map = {o.pk: o for o in rel_model.objects.filter(pk__in=ids)}
            options = []
            for v in ids:
                o = obj_map.get(v)
                if o:
                    options.append({'id': v, 'name': str(o), 'description': getattr(o, 'description', '') or ''})
            return options
        return [{'id': v, 'name': str(v)} for v in ids]

    if not hasattr(model_class, field_lookup):
        return []

    field_obj = None
    try:
        field_obj = model_class._meta.get_field(field_lookup)
    except Exception:
        pass

    if not field_obj:
        return []

    if field_obj.many_to_one or field_obj.one_to_one:
        related_model = field_obj.remote_field.model
        fk_ids = qs.values_list(param_name, flat=True).distinct()
        options = related_model.objects.filter(pk__in=fk_ids).order_by('name')
        return [{'id': o.pk, 'name': str(o), 'description': getattr(o, 'description', '') or ''} for o in options]
    else:
        values = qs.values_list(param_name, flat=True).distinct().order_by(param_name)
        return [{'id': v, 'name': str(v)} for v in values if v is not None]


def _get_node_pages(node: dict) -> list[dict]:
    """Get sub-pages for a node. If no pages defined, create one from param_names."""
    pages = node.get('pages')
    if pages:
        return pages
    param_names = node.get('param_names') or ([node['param_name']] if node.get('param_name') else [])
    if param_names:
        return [{'title': node.get('question', ''), 'param_names': param_names}]
    return []


def _get_page_param_names(node: dict, page_index: int) -> list[str]:
    pages = _get_node_pages(node)
    if 0 <= page_index < len(pages):
        return pages[page_index].get('param_names', [])
    return []


class QuestionGraphConfigView(APIView):
    """GET /api/core/question-graph/<code>/ — graph config + entry node options."""
    permission_classes = []

    def get(self, request, code):
        try:
            graph = QuestionGraph.objects.get(code=code, is_active=True)
        except QuestionGraph.DoesNotExist:
            return Response({'error': 'Graph not found'}, status=404)

        entry_node = graph.get_entry_node()
        if not entry_node:
            return Response({'error': 'No entry node'}, status=400)

        entry_options = _get_options_for_page_node(graph, entry_node, {})

        return Response({
            'graph_code': graph.code,
            'graph_name': graph.name,
            'entry_node_id': graph.graph_json.get('entry_node'),
            'entry_node': entry_node,
            'entry_options': entry_options,
            'graph_json': graph.graph_json,
            'sub_page': 0,
            'total_sub_pages': 1,
            'page_title': entry_node.get('name', entry_node.get('question', '')),
        })


class QuestionGraphAdvanceView(APIView):
    """POST /api/core/question-graph/<code>/advance/ — submit answer, get next node or sub-page."""
    permission_classes = []

    def post(self, request, code):
        try:
            graph = QuestionGraph.objects.get(code=code, is_active=True)
        except QuestionGraph.DoesNotExist:
            return Response({'error': 'Graph not found'}, status=404)

        current_node_id = request.data.get('node_id')
        answers = request.data.get('answers', {})
        accumulated = request.data.get('filters_applied', {})
        sub_page = int(request.data.get('sub_page', 0))

        if not current_node_id:
            return Response({'error': 'node_id required'}, status=400)

        node = graph.get_node(current_node_id)
        if not node:
            return Response({'error': 'Node not found'}, status=400)

        pages = _get_node_pages(node)

        # Save answers from current sub-page
        current_page_params = _get_page_param_names(node, sub_page)
        for pn in current_page_params:
            if pn in answers and answers[pn] is not None:
                accumulated[pn] = answers[pn]

        # Check if there are more sub-pages in this node
        if sub_page + 1 < len(pages):
            next_sub = sub_page + 1
            next_page = pages[next_sub]
            next_options = {}
            for pn in next_page.get('param_names', []):
                opts = _get_options_for_param(graph.equipment_type, pn, accumulated)
                if opts:
                    next_options[pn] = opts

            return Response({
                'terminal': False,
                'entry_node_id': current_node_id,
                'entry_node': node,
                'entry_options': next_options,
                'filters_applied': accumulated,
                'sub_page': next_sub,
                'total_sub_pages': len(pages),
                'page_title': next_page.get('title', node.get('question', '')),
                'default_value': next_page.get('default_value', {}),
            })

        # All sub-pages done → collect answers and move to next node
        # For page nodes: save all params, then follow edges
        if node.get('type') != 'branch':
            for p in node.get('params', []):
                pn = p.get('param_name')
                if pn and pn in answers and answers[pn] is not None:
                    accumulated[pn] = answers[pn]
        # Also save old-format answers
        for pn, val in answers.items():
            if val is not None:
                accumulated[pn] = val

        # Navigate: branch node uses answer value, page node uses edges
        branch_val = None
        if node.get('type') == 'branch':
            branch_val = accumulated.get(node.get('param_name'))
        else:
            # For old format: check branching_param
            branching_param = (pages[0].get('param_names', [None])[0]) if pages else node.get('param_name')
            if branching_param:
                branch_val = answers.get(branching_param)

        next_node = graph.get_next_node(current_node_id, branch_val)
        # Пропускаем branch-узлы: это переходы, а не вопросы мастера.
        # Идём по ответу на param_name ветвления до ближайшей страницы.
        seen = set()
        while next_node is not None and next_node.get('type') == 'branch':
            nid = _get_node_id(graph, next_node)
            if not nid or nid in seen:
                break
            seen.add(nid)
            next_node = graph.get_next_node(nid, accumulated.get(next_node.get('param_name')))
        if next_node is None:
            return Response({
                'terminal': True,
                'filters_applied': accumulated,
            })

        next_options = _get_options_for_page_node(graph, next_node, accumulated)

        return Response({
            'terminal': False,
            'entry_node_id': _get_node_id(graph, next_node),
            'entry_node': next_node,
            'entry_options': next_options,
            'filters_applied': accumulated,
            'sub_page': 0,
            'total_sub_pages': 1,
            'page_title': next_node.get('name', next_node.get('question', '')),
        })


class QuestionGraphResultsView(APIView):
    """POST /api/core/question-graph/<code>/results/ — search models with filters."""
    permission_classes = []

    def post(self, request, code):
        try:
            graph = QuestionGraph.objects.get(code=code, is_active=True)
        except QuestionGraph.DoesNotExist:
            return Response({'error': 'Graph not found'}, status=404)

        filters = request.data.get('filters', {})
        page = int(request.data.get('page', 1))
        page_size = min(int(request.data.get('page_size', 24)), 100)

        content_type = graph.equipment_type.content_type
        if not content_type:
            return Response({'error': 'No content type'}, status=400)

        model_class = content_type.model_class()
        if not model_class:
            return Response({'error': 'No model class'}, status=400)

        qs = model_class.objects.filter(is_active=True)
        for pn, pv in filters.items():
            if pv is None:
                continue
            fd = _find_filter_def(model_class, pn)
            if fd:
                try:
                    lookup, converted = fd.build_filter_lookup(pv)
                    if lookup and converted is not None:
                        qs = qs.filter(**{lookup: converted})
                    continue
                except Exception:
                    pass
            try:
                qs = qs.filter(**{_resolve_field_lookup(model_class, pn): pv})
            except Exception:
                pass

        # JOIN-фильтры (профиль сигналов) — убираем дубликаты строк
        qs = qs.distinct()

        total = qs.count()
        offset = (page - 1) * page_size
        items = list(qs[offset:offset + page_size])

        select_fields = getattr(model_class, 'SELECT_RELATED_FIELDS', None)
        if select_fields:
            order = {i.pk: n for n, i in enumerate(items)}
            items = model_class.objects.filter(pk__in=list(order)).select_related(*select_fields)
            items = sorted(items, key=lambda o: order[o.pk])

        results = []
        for item in items:
            try:
                results.append(item.to_values_dict() if hasattr(item, 'to_values_dict') else item.to_dict())
            except Exception:
                results.append({'id': item.pk, 'name': str(item)})

        # Prices — как в плоском мастере (WizardResultsView)
        currency_code = get_currency_code(request)
        sku_codes = [r.get('sku', {}).get('code') for r in results if isinstance(r.get('sku'), dict) and r['sku'].get('code')]
        prices = get_bulk_prices(sku_codes, currency_code) if sku_codes else {}
        for r in results:
            if isinstance(r.get('sku'), dict):
                r['price'] = prices.get(r['sku'].get('code'))

        return Response({
            'results': results,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': max(1, (total + page_size - 1) // page_size) if total > 0 else 0,
        })


# ── Admin CRUD ──────────────────────────────────────────────

class QuestionGraphAdminListView(APIView):
    """GET /api/core/question-graph/admin/ — list all graphs."""
    permission_classes = []

    def get(self, request):
        graphs = QuestionGraph.objects.select_related('equipment_type').all()
        return Response([{
            'id': g.id,
            'code': g.code,
            'name': g.name,
            'equipment_type_id': g.equipment_type_id,
            'equipment_type_name': g.equipment_type.name if g.equipment_type else '',
            'is_active': g.is_active,
        } for g in graphs])

    def post(self, request):
        graph = QuestionGraph.objects.create(
            code=request.data.get('code', ''),
            name=request.data.get('name', ''),
            equipment_type_id=request.data.get('equipment_type_id'),
            graph_json=request.data.get('graph_json', {}),
            is_active=request.data.get('is_active', True),
        )
        return Response({'id': graph.id, 'code': graph.code}, status=201)


class QuestionGraphAdminDetailView(APIView):
    """GET/PUT/DELETE /api/core/question-graph/admin/<id>/"""
    permission_classes = []

    def get(self, request, graph_id):
        try:
            g = QuestionGraph.objects.get(pk=graph_id)
        except QuestionGraph.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        return Response({
            'id': g.id, 'code': g.code, 'name': g.name,
            'equipment_type_id': g.equipment_type_id,
            'graph_json': g.graph_json, 'is_active': g.is_active,
        })

    def put(self, request, graph_id):
        try:
            g = QuestionGraph.objects.get(pk=graph_id)
        except QuestionGraph.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        for field in ('code', 'name', 'graph_json', 'is_active', 'equipment_type_id'):
            if field in request.data:
                setattr(g, field, request.data[field])
        g.save()
        return Response({'status': 'ok'})

    def delete(self, request, graph_id):
        try:
            g = QuestionGraph.objects.get(pk=graph_id)
        except QuestionGraph.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        g.delete()
        return Response({'status': 'deleted'})


# ── Converter: graph → wizard ───────────────────────────────

class QuestionGraphToWizardView(APIView):
    """POST /api/core/question-graph/<code>/to-wizard/ — generate SelectionWizard from graph."""
    permission_classes = []

    def post(self, request, code):
        try:
            graph = QuestionGraph.objects.get(code=code, is_active=True)
        except QuestionGraph.DoesNotExist:
            return Response({'error': 'Graph not found'}, status=404)

        pages, filters = self._convert(graph)

        wizard, created = SelectionWizard.objects.update_or_create(
            equipment_type=graph.equipment_type,
            defaults={
                'name': graph.name,
                'code': graph.code,
                'steps_json': {'pages': pages, 'filters': filters},
                'is_active': True,
            }
        )

        return Response({
            'wizard_id': wizard.id,
            'created': created,
            'pages': pages,
            'filters': filters,
        })

    @staticmethod
    def _convert(graph):
        """Walk graph nodes, collect pages and filters."""
        pages = []
        filters = []
        step_counter = [0]

        def walk(node_id, visited=None):
            if visited is None:
                visited = set()
            if node_id in visited:
                return
            visited.add(node_id)

            node = graph.get_node(node_id)
            if not node:
                return

            node_pages = _get_node_pages(node)
            for sp in node_pages:
                step_counter[0] += 1
                pages.append({
                    'step_number': step_counter[0],
                    'title': sp.get('title', node.get('question', '')),
                    'description': node.get('description', ''),
                })
                for i, pn in enumerate(sp.get('param_names', [])):
                    filters.append({
                        'param_name': pn,
                        'page': step_counter[0],
                        'order': i + 1,
                        'label': pn,
                    })

            # Follow edges (not branches — linear walk)
            for edge in graph.graph_json.get('edges', []):
                if edge.get('from') == node_id:
                    walk(edge['to'], visited)

        walk(graph.graph_json.get('entry_node'))
        return pages, filters


_FIELD_TO_LOOKUP = {
    'thread_type_id': 'thread__thread_type_id',
}


def _resolve_field_lookup(model_class, param_name):
    """Map param_name to actual Django field lookup (handles cross-FK fields)."""
    return _FIELD_TO_LOOKUP.get(param_name, param_name)


def _get_node_id(graph, node) -> str | None:
    for nid, n in graph.graph_json.get('nodes', {}).items():
        if n is node:
            return nid
    return None


# ═══ Catalog Wizard Adapter ═══

class CatalogWizardAdapterView(APIView):
    """GET /api/core/catalog-wizard/<code>/ — unified wizard config (graph or flat)."""
    permission_classes = []

    def get(self, request, code):
        # 1. Try graph
        try:
            graph = QuestionGraph.objects.get(code=code, is_active=True)
        except QuestionGraph.DoesNotExist:
            graph = None

        if graph:
            return self._graph_config(graph)

        # 2. Fallback to flat wizard
        return self._flat_config(code)

    def _graph_config(self, graph):
        entry_node = graph.get_entry_node()
        if not entry_node:
            return Response({'type': 'graph', 'error': 'No entry node'}, status=400)

        pages = _get_node_pages(entry_node)
        return Response({
            'type': 'graph',
            'config': {
                'graph_code': graph.code,
                'graph_name': graph.name,
                'entry_node_id': graph.graph_json.get('entry_node'),
                'entry_node': entry_node,
                'graph_json': graph.graph_json,
                'sub_page': 0,
                'total_sub_pages': len(pages),
                'page_title': pages[0]['title'] if pages else entry_node.get('question', ''),
            }
        })

    def _flat_config(self, code):
        try:
            from core.models.equipment_type import EquipmentType
            et = EquipmentType.objects.get(code=code)
        except EquipmentType.DoesNotExist:
            return Response({'error': f'Equipment type not found: {code}'}, status=404)

        wizard = SelectionWizard.objects.filter(equipment_type=et, is_active=True).first()
        if wizard:
            pages = wizard.steps_json.get('pages', [])
            filters = wizard.steps_json.get('filters', [])
            return Response({
                'type': 'flat',
                'config': {
                    'wizard_id': wizard.id,
                    'name': wizard.name,
                    'pages': pages,
                    'filters': filters,
                }
            })
        return Response({
            'type': 'flat',
            'config': {
                'wizard_id': None,
                'name': et.name,
                'pages': [],
                'filters': [],
                'warning': 'No wizard or graph configured for this equipment type'
            }
        })
class QuestionGraphVisibleParamsView(APIView):
    permission_classes = []

    def get(self, request, code):
        try:
            graph = QuestionGraph.objects.get(code=code, is_active=True)
        except QuestionGraph.DoesNotExist:
            return Response({"visible": []})
        filters = {}
        for k, v in request.query_params.items():
            if v:
                try: filters[k] = int(v)
                except ValueError: filters[k] = v
        visible = set()
        visited = set()
        cid = graph.graph_json.get("entry_node")
        while cid and cid not in visited:
            visited.add(cid)
            node = graph.get_node(cid)
            if not node: break
            for page in _get_node_pages(node):
                for pn in page.get("param_names", []):
                    visible.add(pn)
            pns = node.get("param_names") or ([node["param_name"]] if node.get("param_name") else [])
            branches = node.get("branches", {})
            if branches and pns:
                val = filters.get(pns[0])
                cid = branches.get(str(val)) if val is not None else branches.get("__default__")
            else:
                found = False
                for e in graph.graph_json.get("edges", []):
                    if e.get("from") == cid:
                        cid = e["to"]; found = True; break
                if not found: break
        return Response({"visible": list(visible)})