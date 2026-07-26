"""Patch ai_assistant/models.py — add fields to existing models."""
import re

path = r'ai_assistant\models.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add selection_tree to AIConversation (after source field block, before created_at)
old1 = '''    source = models.CharField(
        max_length=32,
        choices=[
            ("web_form", "Web Form"),
            ("email", "Email"),
            ("messenger", "Messenger"),
            ("api", "External API"),
        ],
        default="web_form",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)'''
new1 = '''    source = models.CharField(
        max_length=32,
        choices=[
            ("web_form", "Web Form"),
            ("email", "Email"),
            ("messenger", "Messenger"),
            ("api", "External API"),
        ],
        default="web_form",
    )
    selection_tree = models.JSONField(null=True, blank=True, help_text="Keш полного дерева SelectionNode для быстрой отдачи на фронт")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)'''
if old1 in content:
    content = content.replace(old1, new1)
    print('OK: AIConversation.selection_tree added')
else:
    print('MISS: old1 not found')
    idx = content.find('source = models.CharField')
    if idx >= 0:
        print(repr(content[idx:idx+300]))

# 2. Add tree_json and final_selections_json to AIQuerySample (after response_text)
old2 = '''    response_text = models.TextField(null=True, blank=True)
    prompt_template = models.ForeignKey('''
new2 = '''    response_text = models.TextField(null=True, blank=True)
    tree_json = models.JSONField(null=True, blank=True, help_text="Эталонное дерево SelectionNode (для обучения)")
    final_selections_json = models.JSONField(null=True, blank=True, help_text="Эталонные выборы пользователя (для обучения)")
    prompt_template = models.ForeignKey('''
if old2 in content:
    content = content.replace(old2, new2)
    print('OK: AIQuerySample.tree_json + final_selections_json added')
else:
    print('MISS: old2 not found')
    idx = content.find('response_text = models.TextField')
    if idx >= 0:
        print(repr(content[idx:idx+200]))

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('File written')
