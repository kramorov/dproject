# pneumatic_fittings/tests/test_fk_cascade.py
from django.test import TestCase
from params.models import ThreadTypes, ThreadSize
from pneumatic_fittings.models import PneumaticFitting, PneumaticFittingModelLine
from producers.models import Brands


class FK_CascadeFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Типы резьб
        cls.g = ThreadTypes.objects.create(name='G', code='G')
        cls.r = ThreadTypes.objects.create(name='R (BSPT)', code='R')
        cls.npt = ThreadTypes.objects.create(name='NPT', code='NPT')
        cls.m = ThreadTypes.objects.create(name='M', code='M')
        cls.g.compatible_thread_types.add(cls.r)

        # Размеры резьб: диаметр + шаг
        cls.g_18 = ThreadSize.objects.create(
            name='G 1/8"', code='G1/8',
            thread_type=cls.g, thread_diameter=9.7, thread_pitch=1.0
        )
        cls.g_34 = ThreadSize.objects.create(
            name='G 3/4"', code='G3/4',
            thread_type=cls.g, thread_diameter=26.4, thread_pitch=1.814
        )
        cls.r_18 = ThreadSize.objects.create(
            name='R 1/8"', code='R1/8',
            thread_type=cls.r, thread_diameter=9.7, thread_pitch=1.0
        )
        cls.r_34 = ThreadSize.objects.create(
            name='R 3/4"', code='R3/4',
            thread_type=cls.r, thread_diameter=26.4, thread_pitch=1.814
        )
        cls.npt_14 = ThreadSize.objects.create(
            name='NPT 1/4"', code='NPT1/4',
            thread_type=cls.npt, thread_diameter=13.7
        )

        # Общие данные
        cls.brand = Brands.objects.create(name='Test Brand', code='TB')
        cls.line = PneumaticFittingModelLine.objects.create(
            name='Test Line', code='TL', brand=cls.brand
        )

        # Фитинги
        cls.fit_g34 = PneumaticFitting.objects.create(
            name='Fit G 3/4', code='F1',
            model_line=cls.line, brand=cls.brand, thread=cls.g_34
        )
        cls.fit_r34 = PneumaticFitting.objects.create(
            name='Fit R 3/4', code='F2',
            model_line=cls.line, brand=cls.brand, thread=cls.r_34
        )
        cls.fit_g18 = PneumaticFitting.objects.create(
            name='Fit G 1/8', code='F3',
            model_line=cls.line, brand=cls.brand, thread=cls.g_18
        )
        cls.fit_r18 = PneumaticFitting.objects.create(
            name='Fit R 1/8', code='F4',
            model_line=cls.line, brand=cls.brand, thread=cls.r_18
        )
        cls.fit_npt14 = PneumaticFitting.objects.create(
            name='Fit NPT 1/4', code='F5',
            model_line=cls.line, brand=cls.brand, thread=cls.npt_14
        )

    # =================================================================
    # ТЕСТЫ: выбор типа резьбы (родитель) → режим «от родителя»
    # =================================================================

    def test_thread_type_G_returns_G_and_R_all_sizes(self):
        """Тип G → все G + R (без учёта диаметра)"""
        result = PneumaticFitting.filter_by_params({'thread_type_id': self.g.id})
        names = {r['name'] for r in result['data']}
        self.assertIn('Fit G 3/4', names)
        self.assertIn('Fit R 3/4', names)
        self.assertIn('Fit G 1/8', names)
        self.assertIn('Fit R 1/8', names)
        self.assertNotIn('Fit NPT 1/4', names)

    def test_thread_type_NPT_returns_only_NPT(self):
        """NPT без совместимых → только NPT"""
        result = PneumaticFitting.filter_by_params({'thread_type_id': self.npt.id})
        names = {r['name'] for r in result['data']}
        self.assertEqual(names, {'Fit NPT 1/4'})

    # =================================================================
    # ТЕСТЫ: выбор конкретной резьбы (потомок) → режим «от потомка»
    # =================================================================

    def test_thread_G34_returns_G34_and_R34_only(self):
        """G 3/4 → G 3/4 + R 3/4, НЕ G 1/8, НЕ NPT"""
        result = PneumaticFitting.filter_by_params({'thread_id': self.g_34.id})
        names = {r['name'] for r in result['data']}
        self.assertEqual(names, {'Fit G 3/4', 'Fit R 3/4'})

    def test_thread_G18_returns_G18_and_R18_only(self):
        """G 1/8 → G 1/8 + R 1/8, НЕ G 3/4"""
        result = PneumaticFitting.filter_by_params({'thread_id': self.g_18.id})
        names = {r['name'] for r in result['data']}
        self.assertEqual(names, {'Fit G 1/8', 'Fit R 1/8'})

    def test_thread_NPT14_returns_only_NPT14(self):
        """NPT 1/4 без аналогов → только сам"""
        result = PneumaticFitting.filter_by_params({'thread_id': self.npt_14.id})
        names = {r['name'] for r in result['data']}
        self.assertEqual(names, {'Fit NPT 1/4'})

    # =================================================================
    # ТЕСТЫ: get_cascade_options
    # =================================================================

    def test_cascade_options_G_returns_all_G_and_R(self):
        """Дропдаун при типе G → все G + R"""
        opts = PneumaticFitting.get_cascade_options('thread_type_id', self.g.id)
        codes = {o['code'] for o in opts}
        self.assertEqual(codes, {'G1/8', 'G3/4', 'R1/8', 'R3/4'})

    def test_cascade_options_NPT_returns_only_NPT(self):
        """Дропдаун при NPT → только NPT"""
        opts = PneumaticFitting.get_cascade_options('thread_type_id', self.npt.id)
        codes = {o['code'] for o in opts}
        self.assertEqual(codes, {'NPT1/4'})

    def test_cascade_options_unknown_param_returns_empty(self):
        """Несуществующий param_name → пустой список"""
        opts = PneumaticFitting.get_cascade_options('nonexistent', 1)
        self.assertEqual(opts, [])

    # =================================================================
    # ТЕСТ: совместимость ThreadTypes.get_compatible_ids
    # =================================================================

    def test_G_compatible_is_GR(self):
        ids = set(self.g.get_compatible_ids())
        self.assertEqual(ids, {self.g.id, self.r.id})

    def test_NPT_compatible_is_only_self(self):
        ids = set(self.npt.get_compatible_ids())
        self.assertEqual(ids, {self.npt.id})
