# pneumatic_fittings/tests/test_kind_catalogs.py
"""Тесты разделения каталогов фитингов по видам: трубка-резьба / глушитель / заглушка.

Запуск (копия основной БД, без миграций и FK-проверок):
    python manage.py test pneumatic_fittings.tests.test_kind_catalogs \
        --settings pneumatic_fittings.tests.settings

Три каталога над одной моделью PneumaticFitting:
  - /api/pneumatic-fittings/   — только 'fitting-thread-pipe'
  - /api/pneumatic-silencers/  — только 'fitting-silencer'
  - /api/pneumatic-plugs/      — только 'fitting-plug'

Тесты устойчивы к реальным данным в копии БД: динамические счётчики по видам
и изоляция через тестовую серию (model_line_id / brand_id).
"""
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import EquipmentType
from producers.models import Brands
from pneumatic_fittings.models import PneumaticFitting, PneumaticFittingModelLine


def kind_count(code):
    """Число активных позиций вида (вид = equipment_type серии)."""
    return PneumaticFitting.objects.filter(
        model_line__equipment_type__code=code, is_active=True).count()


class KindCatalogTests(TestCase):
    """Каждый каталог выдаёт только позиции своего вида и свой набор фильтров."""

    @classmethod
    def setUpTestData(cls):
        cls.brand = Brands.objects.create(name='_KIND_BRAND', code='_KIND_BRAND')
        cls.et_tube, _ = EquipmentType.objects.get_or_create(
            code='fitting-thread-pipe', defaults={'name': '_Tube type'})
        cls.et_sil, _ = EquipmentType.objects.get_or_create(
            code='fitting-silencer', defaults={'name': '_Silencer type'})
        cls.et_plug, _ = EquipmentType.objects.get_or_create(
            code='fitting-plug', defaults={'name': '_Plug type'})

        cls.line_tube = PneumaticFittingModelLine.objects.create(
            name='_Tube Line', code='_TL', brand=cls.brand, equipment_type=cls.et_tube)
        cls.line_sil = PneumaticFittingModelLine.objects.create(
            name='_Silencer Line', code='_SL', brand=cls.brand, equipment_type=cls.et_sil)
        cls.line_plug = PneumaticFittingModelLine.objects.create(
            name='_Plug Line', code='_PL', brand=cls.brand, equipment_type=cls.et_plug)

        cls.tube = PneumaticFitting.objects.create(
            name='_Tube item', code='_T1', model_line=cls.line_tube,
            equipment_type=cls.et_tube, pipe_diameter=8)
        cls.sil = PneumaticFitting.objects.create(
            name='_Silencer item', code='_S1', model_line=cls.line_sil,
            equipment_type=cls.et_sil, flow_rate=100)
        cls.plug = PneumaticFitting.objects.create(
            name='_Plug item', code='_P1', model_line=cls.line_plug,
            equipment_type=cls.et_plug)

    def setUp(self):
        self.client = APIClient()

    # ── Каталог: вид-скоп ──

    def test_each_catalog_returns_only_its_kind(self):
        for url, code in [
            ('/api/pneumatic-fittings/catalog/', 'fitting-thread-pipe'),
            ('/api/pneumatic-silencers/catalog/', 'fitting-silencer'),
            ('/api/pneumatic-plugs/catalog/', 'fitting-plug'),
        ]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, url)
            self.assertEqual(resp.json()['total'], kind_count(code), url)

    def test_catalog_scoped_by_series_within_kind(self):
        # Серия глушителя в каталоге глушителей → только тестовая позиция
        resp = self.client.get(f'/api/pneumatic-silencers/catalog/?model_line_id={self.line_sil.id}')
        self.assertEqual(resp.json()['total'], 1)
        self.assertEqual(resp.json()['data'][0]['code'], '_S1')

    def test_series_of_other_kind_invisible(self):
        # Серия трубки в каталоге глушителей → 0 позиций
        resp = self.client.get(f'/api/pneumatic-silencers/catalog/?model_line_id={self.line_tube.id}')
        self.assertEqual(resp.json()['total'], 0)

    def test_brand_scope_stays_within_kind(self):
        # Бренд тестовых позиций: в трубном каталоге только трубная позиция
        resp = self.client.get(f'/api/pneumatic-fittings/catalog/?brand_id={self.brand.id}')
        self.assertEqual(resp.json()['total'], 1)
        self.assertEqual(resp.json()['data'][0]['code'], '_T1')

    # ── Фильтры ──

    def test_silencer_filters_exclude_tube_specific(self):
        resp = self.client.get('/api/pneumatic-silencers/filters/')
        self.assertEqual(resp.status_code, 200)
        filters = resp.json()['filters']
        for excluded in ('pipe_diameter', 'pipe_material_id', 'fitting_variety_id', 'swivel'):
            self.assertNotIn(excluded, filters)

    def test_tube_filters_include_tube_specific(self):
        resp = self.client.get('/api/pneumatic-fittings/filters/')
        self.assertEqual(resp.status_code, 200)
        filters = resp.json()['filters']
        self.assertIn('pipe_diameter', filters)
        self.assertIn('swivel', filters)

    # ── Быстрый подбор ──

    def test_quickselect_scoped_by_kind(self):
        for url, code in [
            ('/api/pneumatic-fittings/quickselect/', 'fitting-thread-pipe'),
            ('/api/pneumatic-silencers/quickselect/', 'fitting-silencer'),
            ('/api/pneumatic-plugs/quickselect/', 'fitting-plug'),
        ]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, url)
            self.assertEqual(resp.json()['total'], kind_count(code), url)

    # ── Карточка товара ──

    def test_silencer_detail_visible_in_silencer_catalog(self):
        resp = self.client.get(f'/api/pneumatic-silencers/catalog/{self.sil.id}/')
        self.assertEqual(resp.status_code, 200)

    def test_silencer_detail_not_visible_in_tube_catalog(self):
        resp = self.client.get(f'/api/pneumatic-fittings/catalog/{self.sil.id}/')
        self.assertEqual(resp.status_code, 404)
