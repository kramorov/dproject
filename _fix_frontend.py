"""Fix AiDebugPage.vue: add TreeNodeDisplay import and component registration."""
path = r'frontend\src\pages\AiDebugPage.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

old = "import api from '@/shared/api'\n\nexport default {\n  name: 'AiDebugPage',"
new = "import api from '@/shared/api'\nimport TreeNodeDisplay from '@/components/TreeNodeDisplay.vue'\n\nexport default {\n  name: 'AiDebugPage',\n  components: { TreeNodeDisplay },"

if old in content:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: TreeNodeDisplay registered')
else:
    print('NOT FOUND - trying alternate match')
    idx = content.find("import api from '@/shared/api'")
    if idx >= 0:
        print(repr(content[idx:idx+200]))
