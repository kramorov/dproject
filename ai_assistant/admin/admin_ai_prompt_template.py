import re

from django.contrib import admin
from django.utils.html import format_html

from ..models.ai_prompt_template import AIPromptTemplate


@admin.register(AIPromptTemplate)
class AIPromptTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "version", "intent", "is_active")
    list_filter = ("is_active", "intent")
    search_fields = ("code", "name", "template_text")
    list_editable = ("is_active",)

    readonly_fields = ("compiled_prompt",)

    fieldsets = (
        (None, {
            "fields": ("code", "name", "version", "description", "intent")
        }),
        ("Шаблон", {
            "fields": ("template_text",),
        }),
        ("Скомпилированный промпт (preview)", {
            "fields": ("compiled_prompt",),
            "classes": ("wide",),
        }),
        ("Настройки", {
            "fields": ("is_active", "schema_name", "schema_json"),
        }),
    )

    def compiled_prompt(self, obj):
        """Компилирует шаблон: разрешает {code} через другие AIPromptTemplate.

        Если код не найден в БД — показывает предупреждение.
        Плейсхолдеры без кода (например, {user_text}) остаются как есть.
        """
        if not obj or not obj.template_text:
            return "—"

        template_text = obj.template_text
        placeholders = set(re.findall(r"\{(\w+)\}", template_text))
        if not placeholders:
            return format_html("<pre>{}</pre>", template_text)

        # Batch lookup кодов — исключаем себя (code=None или свой собственный)
        exclude_self = [obj.code] if obj.code else []
        templates = {
            t.code: t.template_text
            for t in AIPromptTemplate.objects.filter(
                code__in=placeholders, is_active=True,
            ).exclude(code__in=exclude_self)
        }

        missing = []
        for ph in sorted(placeholders):
            if ph in templates:
                continue
            # Проверяем: может это системный плейсхолдер (не код шаблона)
            if ph in ("user_text", "requirements", "global_requirements", "text"):
                templates[ph] = "{" + ph + "}"  # оставить как есть
            else:
                missing.append(ph)

        # Собираем результат
        class SafeDict(dict):
            def __missing__(self, key):
                return "{" + key + "}"

        compiled = template_text.format_map(SafeDict(templates))

        # Формируем вывод
        html = f'<pre style="white-space: pre-wrap; font-family: monospace; '
        html += f'background: #f8f9fa; padding: 12px; border-radius: 6px; '
        html += f'max-height: 500px; overflow-y: auto; font-size: 13px; '
        html += f'line-height: 1.5;">{compiled}</pre>'

        if missing:
            html += (
                f'<div style="margin-top: 8px; padding: 8px 12px; '
                f'background: #fff3cd; border: 1px solid #ffc107; '
                f'border-radius: 4px; color: #856404;">'
                f'⚠️ Не найдены в БД: <code>{", ".join(missing)}</code>'
                f'</div>'
            )

        return format_html(html)

    compiled_prompt.short_description = "Скомпилированный промпт"
