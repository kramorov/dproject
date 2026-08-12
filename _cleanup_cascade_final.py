"""One-shot cleanup: remove all remaining CascadeRule references."""
import re

# 1. test_pipeline.py
p = r'ai_assistant\test_pipeline.py'
c = open(p, encoding='utf-8').read()

# Remove import line
c = re.sub(r'\s*CascadeRule,', '', c)

# Remove CascadeRuleTests class block (from "class CascadeRuleTests" to next "\nclass ")
c = re.sub(r'\nclass CascadeRuleTests\(TestCase\):.*?(?=\nclass )', '', c, flags=re.DOTALL)

# Remove remaining standalone CascadeRule.objects.create calls in setUp blocks
c = re.sub(r'\s*CascadeRule\.objects\.create\(.*?\)\n', '\n', c, flags=re.DOTALL)

open(p, 'w', encoding='utf-8').write(c)
print('test_pipeline.py cleaned, remaining:', c.count('CascadeRule'))

# 2. views.py — comment in docstring
p2 = r'ai_assistant\api\views.py'
c2 = open(p2, encoding='utf-8').read()
c2 = c2.replace('через CascadeRule', 'через DerivationRule')
open(p2, 'w', encoding='utf-8').write(c2)
print('views.py remaining CascadeRule:', c2.count('CascadeRule'))
