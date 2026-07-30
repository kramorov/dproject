# Clean debug logs and fix cancel text
f = open('frontend/src/components/bom/CompositionGroupNode.vue', 'r', encoding='utf-8')
c = f.read()
f.close()

# Remove debug from buttons
c = c.replace('@click.stop="console.log(\'CG-delete clicked\', node.id); $emit(\'delete-group\', node.id)"',
              '@click.stop="$emit(\'delete-group\', node.id)"')
c = c.replace('@click="console.log(\'CG-remove-et clicked\', node.id, et.id); $emit(\'remove-et\', node.id, et.id)"',
              '@click="$emit(\'remove-et\', node.id, et.id)"')
c = c.replace('@click.stop="console.log(\'CG-remove-ref clicked\', node.id); $emit(\'remove-reference\', node.id)"',
              '@click.stop="$emit(\'remove-reference\', node.id)"')
c = c.replace('@remove-reference="(id) => { console.log(\'CG-pass-remove-ref\', id); $emit(\'remove-reference\', id) }"',
              '@remove-reference="(id) => $emit(\'remove-reference\', id)"')

f = open('frontend/src/components/bom/CompositionGroupNode.vue', 'w', encoding='utf-8')
f.write(c)
f.close()

# Now BomConfigPage
f = open('frontend/src/pages/admin/BomConfigPage.vue', 'r', encoding='utf-8')
c = f.read()
f.close()

# Remove debug logs
c = c.replace('async deleteGroup(groupId) {\n      console.log("BOM-deleteGroup called", groupId);',
              'async deleteGroup(groupId) {')
c = c.replace('showConfirm({ title, message, subMessage, confirmText, cancelText }) {\n      console.log("BOM-showConfirm", title);',
              'showConfirm({ title, message, subMessage, confirmText, cancelText }) {')
c = c.replace('removeReference(groupId) {\n      console.log("BOM-removeReference called", groupId);',
              'removeReference(groupId) {')
c = c.replace('async removeEquipmentType(groupId, etId) {\n      console.log("BOM-removeEquipmentType", groupId, etId);',
              'async removeEquipmentType(groupId, etId) {')
c = c.replace('@confirm="console.log(\'dialog-confirm\'); confirmDialog.resolve(true)"',
              '@confirm="confirmDialog.resolve(true)"')
c = c.replace('@cancel="console.log(\'dialog-cancel\'); confirmDialog.resolve(false)"',
              '@cancel="confirmDialog.resolve(false)"')

# Fix cancel text for delete operations
c = c.replace('if (!await this.showConfirm({ title: "Удаление", message: "Удалить группу и все вложенные?", confirmText: "Удалить" })) return',
              'if (!await this.showConfirm({ title: "Удаление", message: "Удалить группу и все вложенные?", confirmText: "Удалить", cancelText: "Не удалять" })) return')
c = c.replace('if (!await this.showConfirm({ title: "Удаление", message: "Удалить спецификацию?", confirmText: "Удалить" })) return',
              'if (!await this.showConfirm({ title: "Удаление", message: "Удалить спецификацию?", confirmText: "Удалить", cancelText: "Не удалять" })) return')

f = open('frontend/src/pages/admin/BomConfigPage.vue', 'w', encoding='utf-8')
f.write(c)
f.close()

print('cleaned')
