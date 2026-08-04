"""Remove cell-all ⟳ button column from PermissionsPage.vue."""
p = r'C:\Users\kramo\PycharmProjects\djangoProject1\frontend\src\pages\admin\PermissionsPage.vue'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# Remove the entire cell-all <td> block (the ⟳ button)
old_start = '<td class="cell-all">'
old_end = '</td>'

while old_start in c:
    idx_start = c.find(old_start)
    idx_end = c.find(old_end, idx_start) + len(old_end)
    c = c[:idx_start] + c[idx_end:]

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)

# Verify
with open(p, 'r', encoding='utf-8') as f:
    result = f.read()
print('cell-all removed successfully' if 'cell-all' not in result else 'FAIL: cell-all still present')
