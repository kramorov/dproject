# Temporary: compare installed packages vs requirements.txt
import subprocess, pathlib, re, sys

py = r"C:\Program Files\Python312\python.exe"
out = subprocess.run([py, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
installed = {}
for line in out.splitlines():
    line = line.strip()
    if "==" in line:
        n, v = line.split("==", 1)
        installed[n.lower()] = (n, v)

p = pathlib.Path(r"C:\Users\kramo\PycharmProjects\djangoProject1\requirements.txt")
req = {}
for line in p.read_text(encoding="utf-16").splitlines():
    line = line.strip()
    m = re.match(r"^([A-Za-z0-9_.\-\[\]]+)\s*==\s*([^\s;]+)", line)
    if m:
        req[m.group(1).lower().split("[")[0]] = (m.group(1), m.group(2), line)

mism = [(name, v, installed[key][1]) for key, (name, v, _) in req.items() if key in installed and installed[key][1] != v]
notinstalled = [(name, v) for key, (name, v, _) in req.items() if key not in installed]
missing = [(n, v) for n, v in installed.values() if n.lower().split("[")[0] not in req]

print("VERSION MISMATCHES:")
for n, v, iv in mism:
    print("  file", n, v, "| installed", iv)
print("IN FILE, NOT INSTALLED:")
for n, v in notinstalled:
    print("  ", n, v)
print("INSTALLED, NOT IN FILE (%d):" % len(missing))
for n, v in missing:
    print("  ", n, v)
