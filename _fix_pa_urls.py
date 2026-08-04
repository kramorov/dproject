"""Fix PA constructor URLs and cable-glands duplicate section."""
import os

# 1. Router
rp = r'C:\Users\kramo\PycharmProjects\djangoProject1\frontend\src\router\index.js'
with open(rp, 'r', encoding='utf-8') as f:
    c = f.read()

# Move PA constructors
c = c.replace("path: '/admin/pa-constructor'", "path: '/configurator/pa'")
c = c.replace("path: '/admin/pa-constructor-legacy'", "path: '/configurator/pa-legacy'")
# Fix cable-glands duplicate section in props
c = c.replace(
    "props: { title: 'Кабельные вводы', section: 'catalog_cg' }",
    "props: { title: 'Кабельные вводы' }"
)
with open(rp, 'w', encoding='utf-8') as f:
    f.write(c)
print('Router fixed')

# 2. TopMenu
tp = r'C:\Users\kramo\PycharmProjects\djangoProject1\frontend\src\components\header\TopMenu.vue'
with open(tp, 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace("to:'/admin/pa-constructor'", "to:'/configurator/pa'")
c = c.replace("to:'/admin/pa-constructor-legacy'", "to:'/configurator/pa-legacy'")
with open(tp, 'w', encoding='utf-8') as f:
    f.write(c)
print('TopMenu fixed')
