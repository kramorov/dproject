c = open("frontend/src/pages/AiDebugPage.vue", "r", encoding="utf-8").read()
c = c.replace("Анализ. Займет примерно", "Анализ и подбор параметров. Займет примерно")
open("frontend/src/pages/AiDebugPage.vue", "w", encoding="utf-8").write(c)
print("OK")
