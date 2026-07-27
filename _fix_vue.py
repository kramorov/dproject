c = open("frontend/src/pages/AiDebugPage.vue", "r", encoding="utf-8").read()

# Replace right panel: prompts → skills
old_panel = c[c.find("<!-- Правая панель"):c.find("<!-- Статистика -->")]
new_panel = '''    <!-- Правая панель: скиллы -->
    <div class="panel skills-panel">
      <h3>Скилл</h3>
      <div class="list">
        <div v-for="s in skills" :key="s.id" class="card"
             :class="{ active: selectedSkill && selectedSkill.id === s.id }">
          <label class="card-label">
            <input type="checkbox"
                   :checked="selectedSkill && selectedSkill.id === s.id"
                   @change="selectSkill(s)" />
            {{ s.code || (s.step + ' / ' + (s.equipment_type_detail ? s.equipment_type_detail.name : '*')) }}
          </label>
          <div class="card-meta">{{ s.prompt_template_detail ? s.prompt_template_detail.code || 'prompt #' + s.prompt_template : 'no prompt' }}</div>
        </div>
      </div>
    </div>

'''
c = c.replace(old_panel, new_panel)
c = c.replace('selectedPrompt: null,', 'selectedSkill: null,')
c = c.replace('prompts: [],', 'skills: [],')
c = c.replace("selectPrompt(p) { this.selectedPrompt = (this.selectedPrompt && this.selectedPrompt.id === p.id) ? null : p },",
              "selectSkill(s) { this.selectedSkill = (this.selectedSkill && this.selectedSkill.id === s.id) ? null : s },")
c = c.replace("if (this.selectedPrompt) payload.prompt_id = this.selectedPrompt.id",
              "if (this.selectedSkill && this.selectedSkill.code) payload.skill_code = this.selectedSkill.code")
c = c.replace("async loadPrompts() { const r = await api.get('/ai-assistant/prompts/'); this.prompts = (r.data && r.data.results) || [] },",
              "async loadSkills() { try { const r = await api.get('/ai-assistant/skills/'); this.skills = Array.isArray(r.data) ? r.data : (r.data.results || []) } catch { this.skills = [] } },")
c = c.replace("this.loadPrompts()", "this.loadSkills()")
open("frontend/src/pages/AiDebugPage.vue", "w", encoding="utf-8").write(c)
print("Vue OK")
