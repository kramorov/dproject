# Temporary: align requirements.txt versions with installed environment (UTF-16 preserved)
import subprocess, pathlib, re

py = r"C:\Program Files\Python312\python.exe"
out = subprocess.run([py, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
installed = {}
for line in out.splitlines():
    line = line.strip()
    if "==" in line:
        n, v = line.split("==", 1)
        installed[n.lower()] = v

p = pathlib.Path(r"C:\Users\kramo\PycharmProjects\djangoProject1\requirements.txt")
text = p.read_text(encoding="utf-16")
nl = "\r\n" if "\r\n" in text else "\n"
lines = text.splitlines()

changed = []
new_lines = []
for line in lines:
    m = re.match(r"^(\s*)([A-Za-z0-9_.\-\[\]]+)\s*==\s*([^\s;]+)(.*)$", line)
    if m:
        name = m.group(2).lower().split("[")[0]
        cur = m.group(3)
        if name in installed and installed[name] != cur:
            new_lines.append(m.group(1) + m.group(2) + "==" + installed[name] + m.group(4))
            changed.append((m.group(2), cur, installed[name]))
            continue
    new_lines.append(line)

p.write_text(nl.join(new_lines) + nl, encoding="utf-16")
print("aligned %d lines:" % len(changed))
for n, old, new in changed:
    print("  %s %s -> %s" % (n, old, new))
