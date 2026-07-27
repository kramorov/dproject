"""
Tests for core.access — centralized catalog access control
and catalog views permission classes.
"""
from django.test import TestCase, Client as TestClient, RequestFactory
from django.urls import reverse
from rest_framework.permissions import AllowAny

from core.access import catalog_permission_classes, apply_catalog_visibility


# ═══════════════════════════════════════════════════════════════════
# core.access unit tests
# ═══════════════════════════════════════════════════════════════════

class CatalogPermissionClassesTests(TestCase):
    """Tests for catalog_permission_classes()."""

    def test_returns_allow_any(self):
        classes = catalog_permission_classes()
        self.assertEqual(len(classes), 1)
        self.assertIs(classes[0], AllowAny)

    def test_returns_new_instance_each_call(self):
        a = catalog_permission_classes()
        b = catalog_permission_classes()
        self.assertIsNot(a, b)  # new list each call
        self.assertIs(a[0], AllowAny)
        self.assertIs(b[0], AllowAny)


class ApplyCatalogVisibilityTests(TestCase):
    """Tests for apply_catalog_visibility()."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_same_queryset(self):
        """Stub: queryset returned unchanged."""
        from django.contrib.contenttypes.models import ContentType
        qs = ContentType.objects.all()
        request = self.factory.get('/')
        result = apply_catalog_visibility(request, qs)
        self.assertEqual(result.query, qs.query)  # no filtering applied

    def test_accepts_request_without_customer(self):
        """Should not fail when request has no customer attribute."""
        from django.contrib.contenttypes.models import ContentType
        qs = ContentType.objects.all()
        request = self.factory.get('/')
        result = apply_catalog_visibility(request, qs)
        self.assertIsNotNone(result)

    def test_empty_queryset(self):
        """Empty queryset returned as-is."""
        from django.contrib.contenttypes.models import ContentType
        qs = ContentType.objects.none()
        request = self.factory.get('/')
        result = apply_catalog_visibility(request, qs)
        self.assertEqual(result.count(), 0)


# ═══════════════════════════════════════════════════════════════════
# Catalog views — permission classes
# ═══════════════════════════════════════════════════════════════════

class CatalogViewPermissionsTests(TestCase):
    """Verify all catalog views use catalog_permission_classes()."""

    def _get_view_permission_classes(self, view_class):
        """Extract permission_classes from a view class."""
        classes = getattr(view_class, 'permission_classes', None)
        if classes is None:
            return None
        # May be a list or a callable result
        if callable(classes):
            return classes()
        return classes

    def _assert_uses_catalog_permissions(self, view_class, view_name):
        """Assert view uses AllowAny (catalog_permission_classes stub)."""
        classes = self._get_view_permission_classes(view_class)
        self.assertIsNotNone(
            classes,
            f"{view_name} has no permission_classes"
        )
        self.assertTrue(
            any(p is AllowAny for p in classes),
            f"{view_name} should use AllowAny, got {[type(p).__name__ for p in classes]}"
        )

    def test_gearbox_views_allow_any(self):
        from gearbox.catalog.views_list import GearboxCatalogView
        from gearbox.catalog.views_detail import GearboxDetailView
        from gearbox.catalog.views_filters import GearboxFilterOptionsView
        from gearbox.catalog.views_engineer import GearboxEngineerView
        from gearbox.catalog.views_engineer_filters import GearboxEngineerFilterOptionsView

        for v, name in [
            (GearboxCatalogView, 'GearboxCatalogView'),
            (GearboxDetailView, 'GearboxDetailView'),
            (GearboxFilterOptionsView, 'GearboxFilterOptionsView'),
            (GearboxEngineerView, 'GearboxEngineerView'),
            (GearboxEngineerFilterOptionsView, 'GearboxEngineerFilterOptionsView'),
        ]:
            self._assert_uses_catalog_permissions(v, name)

    def test_filter_regulator_views_allow_any(self):
        from filter_regulator.catalog.views_list import FilterRegulatorCatalogView
        from filter_regulator.catalog.views_detail import FilterRegulatorDetailView
        from filter_regulator.catalog.views_filters import FilterRegulatorFilterOptionsView
        from filter_regulator.catalog.views_engineer import FilterRegulatorEngineerView
        from filter_regulator.catalog.views_engineer_filters import FilterRegulatorEngineerFilterOptionsView

        for v, name in [
            (FilterRegulatorCatalogView, 'FilterRegulatorCatalogView'),
            (FilterRegulatorDetailView, 'FilterRegulatorDetailView'),
            (FilterRegulatorFilterOptionsView, 'FilterRegulatorFilterOptionsView'),
            (FilterRegulatorEngineerView, 'FilterRegulatorEngineerView'),
            (FilterRegulatorEngineerFilterOptionsView, 'FilterRegulatorEngineerFilterOptionsView'),
        ]:
            self._assert_uses_catalog_permissions(v, name)

    def test_solenoid_valves_views_allow_any(self):
        from solenoid_valves.catalog.views_list import SolenoidValvesCatalogView
        from solenoid_valves.catalog.views_detail import SolenoidValvesDetailView
        from solenoid_valves.catalog.views_filters import SolenoidValvesFilterOptionsView
        from solenoid_valves.catalog.views_engineer import SolenoidValvesEngineerView
        from solenoid_valves.catalog.views_engineer_filters import SolenoidValvesEngineerFilterOptionsView

        for v, name in [
            (SolenoidValvesCatalogView, 'SolenoidValvesCatalogView'),
            (SolenoidValvesDetailView, 'SolenoidValvesDetailView'),
            (SolenoidValvesFilterOptionsView, 'SolenoidValvesFilterOptionsView'),
            (SolenoidValvesEngineerView, 'SolenoidValvesEngineerView'),
            (SolenoidValvesEngineerFilterOptionsView, 'SolenoidValvesEngineerFilterOptionsView'),
        ]:
            self._assert_uses_catalog_permissions(v, name)

    def test_pneumatic_fittings_views_allow_any(self):
        from pneumatic_fittings.catalog.views_list import PneumaticFittingsCatalogView
        from pneumatic_fittings.catalog.views_detail import PneumaticFittingsDetailView
        from pneumatic_fittings.catalog.views_filters import PneumaticFittingsFilterOptionsView
        from pneumatic_fittings.catalog.views_engineer import PneumaticFittingsEngineerView
        from pneumatic_fittings.catalog.views_engineer_filters import PneumaticFittingsEngineerFilterOptionsView

        for v, name in [
            (PneumaticFittingsCatalogView, 'PneumaticFittingsCatalogView'),
            (PneumaticFittingsDetailView, 'PneumaticFittingsDetailView'),
            (PneumaticFittingsFilterOptionsView, 'PneumaticFittingsFilterOptionsView'),
            (PneumaticFittingsEngineerView, 'PneumaticFittingsEngineerView'),
            (PneumaticFittingsEngineerFilterOptionsView, 'PneumaticFittingsEngineerFilterOptionsView'),
        ]:
            self._assert_uses_catalog_permissions(v, name)

    def test_limit_switch_views_allow_any(self):
        from pa_controls.catalog.views_list import LimitSwitchBoxCatalogView
        from pa_controls.catalog.views_detail import LimitSwitchBoxDetailView
        from pa_controls.catalog.views_filters import LimitSwitchBoxFilterOptionsView
        from pa_controls.catalog.views_engineer import LimitSwitchBoxEngineerView
        from pa_controls.catalog.views_engineer_filters import LimitSwitchBoxEngineerFilterOptionsView

        for v, name in [
            (LimitSwitchBoxCatalogView, 'LimitSwitchBoxCatalogView'),
            (LimitSwitchBoxDetailView, 'LimitSwitchBoxDetailView'),
            (LimitSwitchBoxFilterOptionsView, 'LimitSwitchBoxFilterOptionsView'),
            (LimitSwitchBoxEngineerView, 'LimitSwitchBoxEngineerView'),
            (LimitSwitchBoxEngineerFilterOptionsView, 'LimitSwitchBoxEngineerFilterOptionsView'),
        ]:
            self._assert_uses_catalog_permissions(v, name)

    def test_engineer_views_no_longer_have_required_section(self):
        """Engineer views should NOT have required_section after migration."""
        from gearbox.catalog.views_engineer import GearboxEngineerView
        from pa_controls.catalog.views_engineer import LimitSwitchBoxEngineerView

        for v in [GearboxEngineerView, LimitSwitchBoxEngineerView]:
            self.assertFalse(
                hasattr(v, 'required_section'),
                f"{v.__name__} still has required_section"
            )


# ═══════════════════════════════════════════════════════════════════
# Catalog API — anonymous access
# ═══════════════════════════════════════════════════════════════════

class CatalogAnonymousAccessTests(TestCase):
    """Verify all catalog endpoints accept anonymous requests (200, not 403)."""

    def setUp(self):
        self.client = TestClient()

    def _assert_accessible(self, url, label):
        resp = self.client.get(url)
        self.assertIn(
            resp.status_code, [200, 404],
            f"{label} ({url}) returned {resp.status_code}, expected 200 or 404"
        )

    def test_gearbox_endpoints_accessible(self):
        self._assert_accessible('/api/gearbox/catalog/', 'gearbox catalog')
        self._assert_accessible('/api/gearbox/filters/', 'gearbox filters')
        self._assert_accessible('/api/gearbox/engineer/', 'gearbox engineer')
        self._assert_accessible('/api/gearbox/engineer/filters/', 'gearbox engineer filters')

    def test_filter_regulator_endpoints_accessible(self):
        self._assert_accessible('/api/filter-regulator/catalog/', 'filter-regulator catalog')
        self._assert_accessible('/api/filter-regulator/filters/', 'filter-regulator filters')
        self._assert_accessible('/api/filter-regulator/engineer/', 'filter-regulator engineer')
        self._assert_accessible('/api/filter-regulator/engineer/filters/', 'filter-regulator engineer filters')

    def test_solenoid_valves_endpoints_accessible(self):
        self._assert_accessible('/api/solenoid-valves/catalog/', 'solenoid valves catalog')
        self._assert_accessible('/api/solenoid-valves/filters/', 'solenoid valves filters')
        self._assert_accessible('/api/solenoid-valves/engineer/', 'solenoid valves engineer')
        self._assert_accessible('/api/solenoid-valves/engineer/filters/', 'solenoid valves engineer filters')

    def test_pneumatic_fittings_endpoints_accessible(self):
        self._assert_accessible('/api/pneumatic-fittings/catalog/', 'pneumatic fittings catalog')
        self._assert_accessible('/api/pneumatic-fittings/filters/', 'pneumatic fittings filters')
        self._assert_accessible('/api/pneumatic-fittings/engineer/', 'pneumatic fittings engineer')
        self._assert_accessible('/api/pneumatic-fittings/engineer/filters/', 'pneumatic fittings engineer filters')

    def test_limit_switch_endpoints_accessible(self):
        self._assert_accessible('/api/pa-controls/catalog/', 'limit switch catalog')
        self._assert_accessible('/api/pa-controls/filters/', 'limit switch filters')
        self._assert_accessible('/api/pa-controls/engineer/', 'limit switch engineer')
        self._assert_accessible('/api/pa-controls/engineer/filters/', 'limit switch engineer filters')
        self._assert_accessible('/api/pa-controls/sections/', 'limit switch sections')
