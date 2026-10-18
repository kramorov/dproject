import sys, io, re
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def probe(path, terms, ctx=240, max_per_term=4):
    print(f"===== {path}")
    doc = fitz.open(path)
    print(f"[pages={doc.page_count}]")
    norm = re.sub(r'\s+', ' ', "\n".join(p.get_text() for p in doc))
    for t in terms:
        hits = 0
        for m in re.finditer(re.escape(t), norm, re.IGNORECASE):
            s = max(0, m.start() - ctx // 2)
            print(f"--- [{t}] ...{norm[s:m.end() + ctx // 2]}...")
            hits += 1
            if hits >= max_per_term:
                break
        if hits == 0:
            print(f"--- [{t}] NOT FOUND")
    doc.close()

if __name__ == "__main__":
    for path, terms in [
        (r"E:\work\Контроль\Проект_приводы\Конкуренты_каталоги\Rotork\PUB002-197-00_0426 IQ3 Pro Range Brochure.pdf",
         ["Remote control", "Maintained", "Pulse", "20 - 60 VDC", "Monitor relay", "Auxiliary"]),
        (r"E:\work\Контроль\Проект_приводы\Конкуренты_каталоги\AUMA\Каталог_технический_AUMA_SA.pdf",
         ["24 V DC", "115 V AC", "230 V AC", "0 – 10 V", "setpoint", "EMERGENCY", "HART", "Profibus DP", "Modbus RTU", "Foundation Fieldbus", "Interlock"]),
        (r"E:\work\Контроль\Проект_приводы\Конкуренты_каталоги\AUMA\HART_AUMA.pdf",
         ["HART", "4 – 20", "point-to-point", "multidrop", "position"]),
        (r"E:\work\Контроль\Проект_приводы\Конкуренты_каталоги\AUMA\FieldBus_AUMA.pdf",
         ["Profibus DP", "Modbus RTU", "Modbus TCP", "Foundation Fieldbus", "HART", "Protocol"]),
    ]:
        try:
            probe(path, terms)
        except Exception as e:
            print(f"ERROR {path}: {e}")
