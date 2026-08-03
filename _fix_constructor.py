p = r'C:\Users\s.kramorov\PycharmProjects\djangoProject1\frontend\src\router\index.js'
c = open(p, encoding='utf-8').read()
c = c.replace("meta: { title: 'Конструктор ПП', role: 'admin' }", "meta: { title: 'Конструктор ПП' }")
c = c.replace("meta: { title: 'Конструктор ЭП', role: 'admin' }", "meta: { title: 'Конструктор ЭП' }")
open(p, 'w', encoding='utf-8').write(c)
print('Done')
