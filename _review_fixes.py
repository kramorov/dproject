# temporary: review fixes L1/L2/L3/M2
import io

CR = '\r\n'


def apply(path, reps):
    t = io.open(path, encoding='utf-8', newline='').read()
    for name, old, new, expected in reps:
        c = t.count(old)
        if c != expected:
            print('PROBLEM %s %s count=%d expected=%d :: %r' % (path, name, c, expected, old[:80]))
            return False
        t = t.replace(old, new)
        print('ok %s %s x%d' % (path, name, c))
    io.open(path, 'w', encoding='utf-8', newline='').write(t)
    print('written', path)
    return True


# ── L1: log instead of silent swallow; L3: blank line, docstring, trailing newline ──
ok1 = apply('pneumatic_fittings/models.py', [
    ('safe_m2m_log',
     "    def _safe_m2m(self, method_name):" + CR +
     "        try:" + CR +
     "            return getattr(self, method_name)()" + CR +
     "        except Exception:" + CR +
     "            return []",
     "    def _safe_m2m(self, method_name):" + CR +
     "        try:" + CR +
     "            return getattr(self, method_name)()" + CR +
     "        except Exception:" + CR +
     "            import logging" + CR +
     "            logging.getLogger('pneumatic_fittings').warning(" + CR +
     "                'Section %s failed for PneumaticFitting #%s', method_name, self.pk, exc_info=True)" + CR +
     "            return []", 1),
    ('blank_before_todict',
     "        ]" + CR + "    def to_dict(self) -> Dict[str , Any] :",
     "        ]" + CR + CR + "    def to_dict(self) -> Dict[str , Any] :", 1),
    ('pressure_docstring',
     "    def pressure_range_display(self) :" + CR +
     '        """Отображаемый диапазон рабочих температур"""',
     "    def pressure_range_display(self) :" + CR +
     '        """Отображаемый диапазон рабочих давлений"""', 1),
])

# trailing newline for models.py
with io.open('pneumatic_fittings/models.py', 'r', encoding='utf-8', newline='') as fh:
    txt = fh.read()
if not txt.endswith('\r\n') and not txt.endswith('\n'):
    with io.open('pneumatic_fittings/models.py', 'a', encoding='utf-8', newline='') as fh:
        fh.write('\r\n')
    print('added trailing newline to models.py')
else:
    print('models.py already ends with newline')

# ── L2: cert_docs filter_horizontal on line admin ──
ok2 = apply('pneumatic_fittings/admin.py', [
    ('filter_horizontal',
     "    filter_horizontal = ('tech_docs',)" + CR + CR +
     "    fieldsets = (" + CR +
     "        (_('Основная информация'), {" + CR +
     "            'fields': ('name', ('code', 'equipment_type'),",
     "    filter_horizontal = ('tech_docs', 'cert_docs')" + CR + CR +
     "    fieldsets = (" + CR +
     "        (_('Основная информация'), {" + CR +
     "            'fields': ('name', ('code', 'equipment_type'),", 1),
])

# ── M2: test creates equipment_type ──
ok3 = apply('pneumatic_fittings/tests/test_fk_cascade.py', [
    ('eq_type_setup',
     "        cls.brand = Brands.objects.create(" + CR +
     "            name='_TEST_FK_CASCADE_BRAND', code='_TFCB'" + CR +
     "        )" + CR +
     "        cls.line = PneumaticFittingModelLine.objects.create(" + CR +
     "            name='_Test Line', code='_TL', brand=cls.brand" + CR +
     "        )",
     "        cls.brand = Brands.objects.create(" + CR +
     "            name='_TEST_FK_CASCADE_BRAND', code='_TFCB'" + CR +
     "        )" + CR +
     "        from core.models import EquipmentType" + CR +
     "        cls.eq_type, _ = EquipmentType.objects.get_or_create(" + CR +
     "            code='_TFCB', defaults={'name': '_TEST_FK_CASCADE_EQ'}" + CR +
     "        )" + CR +
     "        cls.line = PneumaticFittingModelLine.objects.create(" + CR +
     "            name='_Test Line', code='_TL', brand=cls.brand, equipment_type=cls.eq_type" + CR +
     "        )", 1),
    ('fit_g34', "            model_line=cls.line, thread=cls.g_34",
     "            model_line=cls.line, equipment_type=cls.eq_type, thread=cls.g_34", 1),
    ('fit_r34', "            model_line=cls.line, thread=cls.r_34",
     "            model_line=cls.line, equipment_type=cls.eq_type, thread=cls.r_34", 1),
    ('fit_g18', "            model_line=cls.line, thread=cls.g_18",
     "            model_line=cls.line, equipment_type=cls.eq_type, thread=cls.g_18", 1),
    ('fit_r18', "            model_line=cls.line, thread=cls.r_18",
     "            model_line=cls.line, equipment_type=cls.eq_type, thread=cls.r_18", 1),
    ('fit_npt14', "            model_line=cls.line, thread=cls.npt_14",
     "            model_line=cls.line, equipment_type=cls.eq_type, thread=cls.npt_14", 1),
])

print('RESULT:', 'OK' if ok1 and ok2 and ok3 else 'FAIL')
