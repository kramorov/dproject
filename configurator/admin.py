"""Админ-классы для моделей configurator."""
from django.contrib import admin
from configurator.models import (
    AssemblyRequirements,
    ComponentRequirement,
    PropagationRule,
    DerivationRule,
    ParameterRule,
    ParameterBinding,
    FittingPattern,
    FittingPatternItem,
    ParameterSource,
    EquipmentTypeParameter,
)


# ── AssemblyRequirements ──

@admin.register(AssemblyRequirements)
class AssemblyRequirementsAdmin(admin.ModelAdmin):
    list_display = ("name", "composition_group", "status", "created_at")
    list_filter = ("status", "composition_group")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("composition_group", "root_node", "conversation")
    fieldsets = (
        (None, {
            "fields": ("name", "composition_group", "root_node"),
        }),
        ("Требования", {
            "fields": ("global_requirements",),
        }),
        ("Статус и AI", {
            "fields": ("status", "conversation"),
        }),
        ("Служебное", {
            "fields": ("created_at", "updated_at"),
        }),
    )


# ── ComponentRequirement ──

@admin.register(ComponentRequirement)
class ComponentRequirementAdmin(admin.ModelAdmin):
    list_display = ("equipment_type", "path", "status", "assembly")
    list_filter = ("status", "equipment_type")
    search_fields = ("path", "equipment_type__code")
    readonly_fields = ("created_at", "updated_at", "effective_requirements")
    autocomplete_fields = ("assembly", "equipment_type", "composition_group_node", "parent")
    fieldsets = (
        (None, {
            "fields": ("assembly", "equipment_type", "composition_group_node"),
        }),
        ("Дерево", {
            "fields": ("parent", "path", "level", "order"),
        }),
        ("Требования", {
            "fields": ("own_requirements", "effective_requirements", "cascade_params"),
        }),
        ("Результат подбора", {
            "fields": (
                "filter_results",
                "selected_product_type", "selected_product_id", "selected_product_specs",
            ),
        }),
        ("Статус", {
            "fields": ("status",),
        }),
        ("Служебное", {
            "fields": ("created_at", "updated_at"),
        }),
    )


# ── PropagationRule ──

@admin.register(PropagationRule)
class PropagationRuleAdmin(admin.ModelAdmin):
    list_display = ("code", "equipment_type", "param_name", "source", "is_mandatory", "is_active")
    list_filter = ("source", "is_mandatory", "is_active")
    search_fields = ("code", "param_name", "equipment_type__code")
    list_editable = ("is_active",)
    autocomplete_fields = ("equipment_type",)
    fieldsets = (
        (None, {
            "fields": ("code", "equipment_type", "param_name"),
        }),
        ("Источник", {
            "fields": ("source", "source_param", "allow_override"),
        }),
        ("Обязательность", {
            "fields": ("is_mandatory", "mandatory_condition"),
        }),
        ("Приоритет", {
            "fields": ("priority", "is_active"),
        }),
    )


# ── DerivationRule ──

@admin.register(DerivationRule)
class DerivationRuleAdmin(admin.ModelAdmin):
    list_display = ("code", "source_type", "source_product_field", "target_type", "target_param", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "source_type__code", "target_type__code")
    list_editable = ("is_active",)
    autocomplete_fields = ("source_type", "target_type")
    fieldsets = (
        (None, {
            "fields": ("code",),
        }),
        ("Источник", {
            "fields": ("source_type", "source_product_field"),
        }),
        ("Приёмник", {
            "fields": ("target_type", "target_param"),
        }),
        ("Опции", {
            "fields": ("transform", "condition", "priority", "is_active"),
        }),
    )


# ── ParameterRule ──

@admin.register(ParameterRule)
class ParameterRuleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "match_type", "hardness", "relaxation_strategy", "is_active")
    list_filter = ("match_type", "hardness", "relaxation_strategy", "is_active")
    search_fields = ("code", "name")
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {
            "fields": ("code", "name"),
        }),
        ("Семантика сравнения", {
            "fields": ("match_type", "match_config"),
        }),
        ("Жёсткость и релаксация", {
            "fields": ("hardness", "relaxation_strategy", "relaxation_config"),
        }),
        ("Составное правило", {
            "fields": ("parent", "combine"),
            "description": (
                "parent — родительское правило (если это часть composite). "
                "combine — AND/OR для родительского правила с match_type=composite."
            ),
        }),
        ("Приоритет", {
            "fields": ("priority", "is_active"),
        }),
        ("Служебное", {
            "fields": ("created_at", "updated_at"),
        }),
    )


# ── ParameterBinding ──

@admin.register(ParameterBinding)
class ParameterBindingAdmin(admin.ModelAdmin):
    list_display = ("equipment_type", "param_name", "rule", "is_active")
    list_filter = ("is_active",)
    search_fields = ("equipment_type__code", "param_name", "rule__code")
    list_editable = ("is_active",)
    autocomplete_fields = ("rule", "equipment_type")
    fieldsets = (
        (None, {
            "fields": ("rule", "equipment_type", "param_name"),
        }),
        ("Статус", {
            "fields": ("is_active",),
        }),
    )


# ── FittingPattern ──

class FittingPatternItemInline(admin.TabularInline):
    model = FittingPatternItem
    extra = 1
    autocomplete_fields = ("equipment_type",)
    fields = ("equipment_type", "quantity", "config", "order")


@admin.register(FittingPattern)
class FittingPatternAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "applies_to", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    list_editable = ("is_active",)
    inlines = (FittingPatternItemInline,)
    autocomplete_fields = ("applies_to",)
    fieldsets = (
        (None, {
            "fields": ("code", "name", "applies_to"),
        }),
        ("Условие", {
            "fields": ("condition",),
        }),
        ("Статус", {
            "fields": ("is_active",),
        }),
    )


# FittingPatternItem — регистрируем отдельно для прямого доступа,
# но основное редактирование через inline в FittingPatternAdmin.
@admin.register(FittingPatternItem)
class FittingPatternItemAdmin(admin.ModelAdmin):
    list_display = ("pattern", "equipment_type", "quantity", "order")
    list_filter = ("pattern",)
    search_fields = ("pattern__code", "equipment_type__code")
    autocomplete_fields = ("pattern", "equipment_type")
    fieldsets = (
        (None, {
            "fields": ("pattern", "equipment_type", "quantity"),
        }),
        ("Конфигурация", {
            "fields": ("config", "order"),
        }),
    )


# ── ParameterSource ──

@admin.register(ParameterSource)
class ParameterSourceAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


# ── EquipmentTypeParameter ──

@admin.register(EquipmentTypeParameter)
class EquipmentTypeParameterAdmin(admin.ModelAdmin):
    list_display = ("code", "equipment_type", "param_name", "is_required", "is_active")
    list_filter = ("is_required", "is_active", "equipment_type")
    search_fields = ("code", "param_name", "equipment_type__code")
    list_editable = ("is_active",)
    autocomplete_fields = ("equipment_type", "parameter_rule")
    fieldsets = (
        (None, {
            "fields": ("code", "equipment_type", "param_name", "label", "field_type"),
        }),
        ("Каталог (FilterDefinition)", {
            "fields": ("filter_type", "data_source_type", "options_source", "options_config"),
        }),
        ("Модель продукта", {
            "fields": ("product_model", "product_model_ref", "field_path"),
        }),
        ("Обязательность", {
            "fields": ("is_required", "required_condition", "priority"),
        }),
        ("Сравнение", {
            "fields": ("parameter_rule",),
        }),
        ("Семантика (AI)", {
            "fields": ("param_type", "unit", "description", "enum_values", "ai_extraction_hint"),
        }),
        ("Опции формы", {
            "fields": ("options_source", "options_config"),
        }),
        ("Служебное", {
            "fields": ("sorting_order", "is_active"),
        }),
    )
