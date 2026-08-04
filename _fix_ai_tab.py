"""Fix AI tab in all catalog App.vue files — add goToAi + AiPlaceholder."""
import os, re

BASE = r'C:\Users\kramo\PycharmProjects\djangoProject1\frontend\src\apps'

EQ_NAMES = {
    'pneumatic-fittings-catalog': 'Пневмофитинги',
    'gearbox-catalog': 'Ручные дублёры',
    'filter-regulator-catalog': 'Фильтр-регуляторы',
    'solenoid-valves-catalog': 'Соленоидные клапаны',
    'pa-catalog': 'Пневмоприводы',
}

for app, eq_name in EQ_NAMES.items():
    p = os.path.join(BASE, app, 'App.vue')
    if not os.path.exists(p):
        print(f'SKIP: {app} — no App.vue')
        continue
    
    with open(p, 'r', encoding='utf-8') as f:
        c = f.read()
    
    changed = False
    
    # 1. Fix @ai handler
    if '@ai="goToSection"' in c:
        c = c.replace('@ai="goToSection"', '@ai="goToAi"')
        changed = True
        print(f'  [1] @ai handler: goToSection -> goToAi')
    
    # 2. Add AiPlaceholder block before </KeepAlive>
    ai_block = f'''    <AiPlaceholder
      v-else-if="page === 'ai'"
      :labels="labels.ai || {{}}"
      eq-name="{eq_name}"
    />
'''
    if 'AiPlaceholder' not in c and '</KeepAlive>' in c:
        c = c.replace('    </KeepAlive>', ai_block + '    </KeepAlive>')
        changed = True
        print(f'  [2] Added AiPlaceholder block')
    
    # 3. Add AiPlaceholder import
    if 'import WizardSelection' in c and 'import AiPlaceholder' not in c:
        c = c.replace(
            'import WizardSelection from',
            'import AiPlaceholder from \'@/shared/components/catalog/AiPlaceholder.vue\'\nimport WizardSelection from'
        )
        changed = True
        print(f'  [3] Added AiPlaceholder import')
    
    # 4. Add goToAi function
    if 'function goToAi' not in c:
        # Find where goToWizard is defined and add goToAi after it
        go_to_wizard_pattern = r'function goToWizard\(\) \{.*?\n  \}'
        match = re.search(go_to_wizard_pattern, c, re.DOTALL)
        if match:
            end_pos = match.end()
            go_to_ai = '''\nfunction goToAi() { previousPage.value = page.value; page.value = 'ai' }'''
            c = c[:end_pos] + go_to_ai + c[end_pos:]
            changed = True
            print(f'  [4] Added goToAi function')
        else:
            # Fallback: add before the closing </script> in the script section
            # Find where 'function goToWizard' or similar function ends
            print(f'  [4] WARNING: could not find goToWizard, adding at end of functions')
            c = c.replace('function goToWizard()', '''function goToAi() { previousPage.value = page.value; page.value = 'ai' }
function goToWizard()''')
    
    if changed:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(c)
        print(f'OK: {app}')
    else:
        print(f'NO CHANGES: {app}')
    
print('\nDone')
