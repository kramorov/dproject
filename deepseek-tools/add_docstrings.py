"""
Добавляет модульные и классовые докстринги в cert_doc/models.py.

Использование:
    python deepseek-tools/_add_docstrings.py

Заменяет:
    - # cert_doc/models.py → многострочный модульный докстринг
    - """Тип сертификата""" → развёрнутый докстринг CertVariety
    - """Базовая модель сертификата""" → развёрнутый докстринг CertData

Идемпотентен: повторный запуск не дублирует (ищет точные старые строки).
"""
import os

path = os.path.join(os.path.dirname(__file__), '..', 'cert_doc', 'models.py')
path = os.path.normpath(path)

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Module docstring
old = "# cert_doc/models.py\n\nfrom django.db import models"
new = ('"""\n'
       'Сертификаты и декларации соответствия.\n'
       '\n'
       'Модели:\n'
       '    CertVariety  - тип сертификата (ТР ТС 012, декларация, ...)\n'
       '    CertData     - сертификат: реквизиты, сроки, типы оборудования\n'
       '\n'
       'Архитектура связей:\n'
       '    CertData.equipment_types  - M2M -> EquipmentType\n'
       '    EquipmentTypeMixin.cert_docs - M2M <- CertData\n'
       '    Прямая:  model_line.cert_docs.all()\n'
       '    Обратная: cert.<model>_related.all()\n'
       '"""\n'
       '\n'
       'from django.db import models')
content = content.replace(old, new, 1)

# 2. CertVariety
old = 'class CertVariety(BaseAbstractModel) :\n    """Тип сертификата"""'
new = ('class CertVariety(BaseAbstractModel) :\n'
       '    """\n'
       '    Тип (разновидность) сертификата.\n'
       '\n'
       '    Примеры: ТР ТС 012/2011, Декларация соответствия, Сертификат ISO.\n'
       '\n'
       '    Поля:\n'
       '        name - название типа\n'
       '        code - код\n'
       '    """')
content = content.replace(old, new, 1)

# 3. CertData
old = 'class CertData(SmartCatalogMixin, BaseAbstractModel , StructuredDataMixin) :\n    """Базовая модель сертификата"""'
new = ('class CertData(SmartCatalogMixin, BaseAbstractModel , StructuredDataMixin) :\n'
       '    """\n'
       '    Сертификат (или декларация) соответствия на оборудование.\n'
       '\n'
       '    Поля:\n'
       '        name              - название\n'
       '        code              - код/номер\n'
       '        description       - описание (серии, бренды)\n'
       '        cert_variety      - FK -> CertVariety\n'
       '        issued_by         - кем выдан\n'
       '        valid_from/until  - срок действия\n'
       '        brand             - FK -> Brands\n'
       '        equipment_types   - M2M -> EquipmentType\n'
       '        media_item        - FK -> MediaLibraryItem (файл PDF)\n'
       '        public_url        - URL\n'
       '\n'
       '    Фильтрация (SmartCatalogMixin):\n'
       '        Тип сертификата, бренд, тип оборудования.\n'
       '        Поиск: name / code / description / issued_by.\n'
       '    """')
content = content.replace(old, new, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("OK")
