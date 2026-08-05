"""API views for QuestionGraph — question-based selection wizard with sub-pages."""
from rest_framework.views import APIView
from rest_framework.response import Response

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

    # Resolve field lookup (handles cross-FK params like thread_type_id)
    field_lookup = _FIELD_LOOKUP.get(param_name, param_name.replace('_id', ''))

    # For dotted lookups (e.g., thread__thread_type), get distinct values from qs
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
            return [{'id': v, 'name': str(o)} for v in ids if (o := rel_model.objects.filter(pk=v).first())]
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
        return [{'id': o.pk, 'name': str(o)} for o in options]
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

        pages = _get_node_pages(entry_node)
        entry_options = {}
        if pages:
            for pn in pages[0].get('param_names', []):
                opts = _get_options_for_param(graph.equipment_type, pn)
                if opts:
                    entry_options[pn] = opts

        return Response({
            'graph_code': graph.code,
            'graph_name': graph.name,
            'entry_node_id': graph.graph_json.get('entry_node'),
            'entry_node': entry_node,
            'entry_options': entry_options,
            'graph_json': graph.graph_json,
            'sub_page': 0,
            'total_sub_pages': len(pages),
            'page_title': pages[0]['title'] if pages else entry_node.get('question', ''),
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
                'node_id': current_node_id,
                'node': node,
                'options': next_options,
                'filters_applied': accumulated,
                'sub_page': next_sub,
                'total_sub_pages': len(pages),
                'page_title': next_page.get('title', node.get('question', '')),
            })

        # All sub-pages done → move to next node
        branching_param = (pages[0].get('param_names', [None])[0]) if pages else node.get('param_name')
        branching_value = answers.get(branching_param) if branching_param else None
        next_node = graph.get_next_node(current_node_id, branching_value)

        if next_node is None:
            return Response({
                'terminal': True,
                'filters_applied': accumulated,
            })

        next_pages = _get_node_pages(next_node)
        next_options = {}
        if next_pages:
            for pn in next_pages[0].get('param_names', []):
                opts = _get_options_for_param(graph.equipment_type, pn, accumulated)
                if opts:
                    next_options[pn] = opts

        return Response({
            'terminal': False,
            'node_id': _get_node_id(graph, next_node),
            'node': next_node,
            'options': next_options,
            'filters_applied': accumulated,
            'sub_page': 0,
            'total_sub_pages': len(next_pages),
            'page_title': next_pages[0].get('title', next_node.get('question', '')) if next_pages else next_node.get('question', ''),
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

        total = qs.count()
        offset = (page - 1) * page_size
        items = list(qs[offset:offset + page_size])

        select_fields = getattr(model_class, 'SELECT_RELATED_FIELDS', None)
        if select_fields:
            items = model_class.objects.filter(pk__in=[i.pk for i in items]).select_related(*select_fields)

        results = []
        for item in items:
            d = {'id': item.pk, 'name': str(item)}
            if hasattr(item, 'code'):
                d['code'] = item.code
            results.append(d)

        return Response({
            'results': results,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size if total else 0,
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
