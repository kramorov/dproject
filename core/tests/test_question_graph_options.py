"""
Tests for the graph wizard (QuestionGraph) option enrichment and params-format nodes.

Usage (one module at a time, per project test harness):
    python manage.py test core.tests.test_question_graph_options \
        --settings pneumatic_fittings.tests.settings --keepdb --verbosity=1
"""
import json, os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
import django
django.setup()

from django.test import TestCase, Client

from core.models.equipment_type import EquipmentType
from core.question_graph_views import _get_options_for_param


class QuestionGraphTests(TestCase):
    """Опции графового мастера (description) и формат params.

    Все тесты в одном классе: кастомный раннер проекта закрывает соединение
    между классами (см. SESSION.md), поэтому несколько классов в модуле
    падают с «Cannot operate on a closed database».
    """

    def test_fk_options_carry_description_key(self):
        """Every FK option must include a 'description' key."""
        et = EquipmentType.objects.get(code='lsb')  # БКВ
        options = _get_options_for_param(et, 'sensor_variety_id')
        self.assertTrue(options, 'ожидались опции sensor_variety_id')
        for opt in options:
            self.assertIn('description', opt, f'опция без description: {opt}')

    def test_fk_options_have_meaningful_description(self):
        """At least one option must have a description that differs from its name."""
        et = EquipmentType.objects.get(code='lsb')
        options = _get_options_for_param(et, 'sensor_variety_id')
        self.assertTrue(
            any(o.get('description') and o['description'] != o['name'] for o in options),
            'ожидалось хотя бы одно содержательное описание',
        )


    def test_config_serves_params_format_with_options(self):
        """Config endpoint отдаёт узел с params и опции для каждого param_name."""
        client = Client()
        resp = client.get('/api/core/question-graph/manual-override/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        entry = data['entry_node']
        self.assertIn('params', entry, 'ожидался формат params')
        names = [p['param_name'] for p in entry['params']]
        self.assertTrue(names, 'params пуст')
        for pn in names:
            self.assertIn(pn, data['entry_options'], f'нет опций для {pn}')

    def test_advance_with_answers_reaches_terminal(self):
        """Одноузловой граф: advance с ответами на все params → terminal."""
        client = Client()
        cfg = client.get('/api/core/question-graph/manual-override/').json()
        entry = cfg['entry_node']
        answers = {}
        for p in entry['params']:
            opts = cfg['entry_options'].get(p['param_name'], [])
            if opts:
                answers[p['param_name']] = opts[0]['id']
        self.assertTrue(answers, 'не удалось собрать ответы')
        resp = client.post(
            '/api/core/question-graph/manual-override/advance/',
            data=json.dumps({
                'node_id': cfg['entry_node_id'],
                'answers': answers,
                'filters_applied': {},
                'sub_page': 0,
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('terminal'), f'ожидался terminal: {data}')
        self.assertTrue(data.get('filters_applied'), 'filters_applied пуст')

    def test_branch_nodes_are_skipped_in_advance(self):
        """branch-узел — это переход, а не вопрос: после ответа идём сразу на страницу."""
        client = Client()
        cfg = client.get('/api/core/question-graph/lsb/').json()
        resp = client.post(
            '/api/core/question-graph/lsb/advance/',
            data=json.dumps({
                'node_id': cfg['entry_node_id'],
                'answers': {'sensor_variety_id': 2},
                'filters_applied': {},
                'sub_page': 0,
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data.get('terminal'))
        self.assertEqual(data['entry_node_id'], 'page_common')
        self.assertEqual(data['entry_node']['type'], 'page')

    def test_results_return_full_cards_with_price(self):
        """Результаты — полные карточки (sku/images/price), как в плоском мастере."""
        client = Client()
        resp = client.post(
            '/api/core/question-graph/lsb/results/',
            data=json.dumps({
                'filters': {'sensor_variety_id': 2},
                'page': 1,
                'page_size': 5,
            }),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['results'], 'ожидались результаты')
        first = data['results'][0]
        self.assertIn('sku', first)
        self.assertIn('images', first)
        self.assertIn('price', first)
