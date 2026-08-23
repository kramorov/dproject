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

        # Общие данные — отдельный бренд чтобы изолировать от реальных данных
        cls.brand = Brands.objects.create(
            name='_TEST_FK_CASCADE_BRAND', code='_TFCB'
        )
        from core.models import EquipmentType
        cls.eq_type, _ = EquipmentType.objects.get_or_create(
            code='_TFCB', defaults={'name': '_TEST_FK_CASCADE_EQ'}
        )
        cls.line = PneumaticFittingModelLine.objects.create(
            name='_Test Line', code='_TL', brand=cls.brand, equipment_type=cls.eq_type
        )

        # Фитинги
        cls.fit_g34 = PneumaticFitting.objects.create(
            name='_Fit G 3/4', code='_F_G34',
            model_line=cls.line, equipment_type=cls.eq_type, thread=cls.g_34
        )
        cls.fit_r34 = PneumaticFitting.objects.create(
            name='_Fit R 3/4', code='_F_R34',
            model_line=cls.line, equipment_type=cls.eq_type, thread=cls.r_34
        )
        cls.fit_g18 = PneumaticFitting.objects.create(
            name='_Fit G 1/8', code='_F_G18',
            model_line=cls.line, equipment_type=cls.eq_type, thread=cls.g_18
        )
        cls.fit_r18 = PneumaticFitting.objects.create(
            name='_Fit R 1/8', code='_F_R18',
            model_line=cls.line, equipment_type=cls.eq_type, thread=cls.r_18
        )
        cls.fit_npt14 = PneumaticFitting.objects.create(
            name='_Fit NPT 1/4', code='_F_N14',
            model_line=cls.line, equipment_type=cls.eq_type, thread=cls.npt_14
        )

    # =================================================================
    # Хелпер: фильтр + изоляция по бренду
    # =================================================================

    def _filter(self, extra_params):
        """filter_by_params с изоляцией на тестовый бренд"""
        params = {'brand_id': self.brand.id, 'limit': 100}
        params.update(extra_params)
        return PneumaticFitting.filter_by_params(params)

    # =================================================================
    # ТЕСТЫ: выбор типа резьбы (родитель) → режим «от родителя»
    # =================================================================

    def test_thread_type_G_returns_G_and_R_all_sizes(self):
        """Тип G → все G + R (без учёта диаметра)"""
        result = self._filter({'thread_type_id': self.g.id})
        codes = {r['code'] for r in result['data']}
        self.assertEqual(codes, {'_F_G34', '_F_R34', '_F_G18', '_F_R18'})

    def test_thread_type_NPT_returns_only_NPT(self):
        """NPT без совместимых → только NPT"""
        result = self._filter({'thread_type_id': self.npt.id})
        codes = {r['code'] for r in result['data']}
        self.assertEqual(codes, {'_F_N14'})

    # =================================================================
    # ТЕСТЫ: выбор конкретной резьбы (потомок) → режим «от потомка»
    # =================================================================

    def test_thread_G34_returns_G34_and_R34_only(self):
        """G 3/4 → точное G 3/4 + совместимое R 3/4, НЕ G 1/8, НЕ NPT"""
        result = self._filter({'thread_id': self.g_34.id})
        exact = {r['code'] for r in result['data']}
        compatible = {r['code'] for r in result.get('compatible_data', [])}
        self.assertEqual(exact, {'_F_G34'})
        self.assertEqual(compatible, {'_F_R34'})

    def test_thread_G18_returns_G18_and_R18_only(self):
        """G 1/8 → точное G 1/8 + совместимое R 1/8, НЕ G 3/4"""
        result = self._filter({'thread_id': self.g_18.id})
        exact = {r['code'] for r in result['data']}
        compatible = {r['code'] for r in result.get('compatible_data', [])}
        self.assertEqual(exact, {'_F_G18'})
        self.assertEqual(compatible, {'_F_R18'})

    def test_thread_NPT14_returns_only_NPT14(self):
        """NPT 1/4 без аналогов → только сам"""
        result = self._filter({'thread_id': self.npt_14.id})
        codes = {r['code'] for r in result['data']}
        self.assertEqual(codes, {'_F_N14'})

    # =================================================================
    # ТЕСТЫ: get_filtered_threads (дропдаун — без смешивания, только свой тип)
    # =================================================================

    def test_get_filtered_threads_G_returns_only_G(self):
        """Дропдаун при типе G → только G (R не показываем)"""
        sizes = PneumaticFitting.get_filtered_threads(self.g.id)
        codes = {s['code'] for s in sizes}
        self.assertEqual(codes, {'G1/8', 'G3/4'})

    def test_get_filtered_threads_NPT_returns_only_NPT(self):
        """Дропдаун при NPT → только NPT"""
        sizes = PneumaticFitting.get_filtered_threads(self.npt.id)
        codes = {s['code'] for s in sizes}
        self.assertEqual(codes, {'NPT1/4'})

    def test_get_filtered_threads_unknown_returns_empty(self):
        """Несуществующий thread_type → пустой список"""
        sizes = PneumaticFitting.get_filtered_threads(99999)
        self.assertEqual(sizes, [])

    # =================================================================
    # ТЕСТ: совместимость ThreadTypes.get_compatible_ids
    # =================================================================

    def test_G_compatible_is_GR(self):
        ids = set(self.g.get_compatible_ids())
        self.assertEqual(ids, {self.g.id, self.r.id})

    def test_NPT_compatible_is_only_self(self):
        ids = set(self.npt.get_compatible_ids())
        self.assertEqual(ids, {self.npt.id})
