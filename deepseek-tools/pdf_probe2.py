import sys, io, re
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def probe(path, terms, ctx=260, max_per_term=5):
    print(f"===== {path}")
    doc = fitz.open(path)
    print(f"[pages={doc.page_count}]")
    full = []
    for p in doc:
        full.append(p.get_text())
    norm = re.sub(r'\s+', ' ', "\n".join(full))
    for t in terms:
        hits = 0
        for m in re.finditer(re.escape(t), norm, re.IGNORECASE):
            s = max(0, m.start() - ctx // 2)
            snippet = norm[s:m.end() + ctx // 2]
            print(f"--- [{t}] ...{snippet}...")
            hits += 1
            if hits >= max_per_term:
                break
        if hits == 0:
            print(f"--- [{t}] NOT FOUND")
    doc.close()

if __name__ == "__main__":
    for path, terms in [
        (r"E:\work\Контроль\Проект_приводы\Конкуренты_каталоги\Rotork\PUB002-197-00_0426 IQ3 Pro Range Brochure.pdf",
         ["CPT", "position transmitter", "HART", "Pakscan", "control voltage", "S1", "torque feedback", "Modbus", "Profibus", "Foundation Fieldbus", "ESD", "partial stroke"]),
        (r"E:\work\Контроль\Проект_приводы\Конкуренты_каталоги\AUMA\ba_asr0_vmmc1_ru.pdf",
         ["24 V DC", "115 V", "230 V", "4 – 20 мА", "0 – 10", "задание", "уставк", "EMERGENCY", "HART", "Profibus", "Modbus"]),
    ]:
        try:
            probe(path, terms)
        except Exception as e:
            print(f"ERROR {path}: {e}")
