"""
ai_assistant/object_registry.py — System objects for AI assistant.
"""
from core.object_registry import register_object

register_object(codename='ai.pipelines', name='Настройка Pipeline', type='admin_page', parent='ai')
register_object(codename='ai.skills', name='Настройка Skills', type='admin_page', parent='ai')
register_object(codename='ai.wizard', name='Мастер подбора (AI)', type='admin_page', parent='ai')
register_object(codename='ai.debug', name='Отладка AI', type='admin_page', parent='ai')
register_object(codename='ai.assistant', name='AI Ассистент', type='page', parent='ai')
