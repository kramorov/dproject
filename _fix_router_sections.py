"""Fix two wrong section assignments in router."""
p = r'C:\Users\kramo\PycharmProjects\djangoProject1\frontend\src\router\index.js'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# PA legacy page should be configurator_pa
c = c.replace(
    "section: 'configurator_ea' } },\n  { path: '/admin/ea-constructor'",
    "section: 'configurator_pa' } },\n  { path: '/admin/ea-constructor'"
)
# Actually the PA legacy line was wrong - let me just target by path
import re
# Fix: pa-constructor-legacy should be configurator_pa
c = re.sub(
    r"(path: '/admin/pa-constructor-legacy'.*?)section: 'configurator_ea'",
    r"\1section: 'configurator_pa'",
    c
)
# Fix: ea-wirings should be configurator_ea
c = re.sub(
    r"(path: '/admin/ea-wirings'.*?)section: 'configurator_pa'",
    r"\1section: 'configurator_ea'",
    c
)

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)
print('Fixed section assignments')
