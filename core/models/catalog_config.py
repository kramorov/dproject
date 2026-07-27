# core/models/catalog_config.py
"""
Unified catalog configuration.

FilterSet  — which filters, scoped or global, exact/compatible flag.
CatalogConfig — all configuration for one equipment type:
                model classes, filter sets per page, ORM hints, labels.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type

from django.db.models import Model, QuerySet

from core.models.filter_definition import FilterDefinition


@dataclass
class FilterSet:
    """A named set of filter definitions for a specific page/scope.

    Attributes:
        definitions: FilterDefinition objects to expose on this page.
        scoped: If True, filter option values are limited to a model_line
                (queryset filtered by model_line_id).
        show_compatible: If True, the frontend may request exact/compatible
                         splitting via ?show_compatible=true.
    """
    definitions: List[FilterDefinition]
    scoped: bool = False
    show_compatible: bool = False


@dataclass
class CatalogConfig:
    """Complete configuration for one equipment catalog.

    Usage (gearbox example):

        GEARBOX_CONFIG = CatalogConfig(
            model_class=GearBox,
            model_line_class=GearBoxModelLine,
            filter_sets={
                'list': FilterSet(
                    definitions=[fd_ip, fd_temp_min, ...],
                    scoped=False,
                    show_compatible=True,
                ),
                'model_line': FilterSet(
                    definitions=[fd_ip, fd_temp_min, ...],  # no brand_id
                    scoped=True,
                    show_compatible=True,
                ),
                'quickselect': FilterSet(
                    definitions=[fd_material, fd_torque, fd_plate],
                    scoped=True,
                    show_compatible=False,
                ),
            },
            select_related=[...],
            prefetch_fields=[...],
            search_fields=[...],
            labels={'title': 'Редукторы', ...},
        )

    Visibility scope:
        Delegates to core.access.apply_catalog_visibility() — the centralized
        access control point for all catalog endpoints.
        Currently: no restrictions (AllowAny stub).
        Future: reads request.customer and applies brand/series filters.
    """

    # ── Models ──
    model_class: Type[Model]
    model_line_class: Optional[Type[Model]] = None

    # ── Filters per page (positive definition, no scope_exclude) ──
    filter_sets: Dict[str, FilterSet] = field(default_factory=dict)

    # ── ORM optimization hints ──
    select_related: List[str] = field(default_factory=list)
    prefetch_fields: List[str] = field(default_factory=list)
    search_fields: List[str] = field(default_factory=list)

    # ── UI labels ──
    labels: Dict[str, str] = field(default_factory=dict)

    # ── Visibility scope (Layer 0) ──

    def apply_visibility_scope(self, queryset: QuerySet, request) -> QuerySet:
        """
        Restrict queryset to allowed brands/series before user filters.

        Delegates to core.access.apply_catalog_visibility().
        Currently: no restrictions (AllowAny stub).
        Future: reads request.customer and applies brand/series filters
                per access.md §7.
        """
        from core.access import apply_catalog_visibility
        return apply_catalog_visibility(request, queryset)

    def get_filter_set(self, scope: str) -> FilterSet:
        """Return the FilterSet for a given scope, or the 'list' default."""
        return self.filter_sets.get(scope, self.filter_sets.get('list'))

    def get_scoped_queryset(self, model_line_id=None) -> QuerySet:
        """Return base queryset, optionally scoped to model_line."""
        qs = self.model_class.objects.filter(is_active=True)
        if model_line_id:
            qs = qs.filter(model_line_id=model_line_id)
        return qs
