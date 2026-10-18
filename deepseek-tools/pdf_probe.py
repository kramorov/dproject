import sys, io, re
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def probe(path, terms, ctx=260, max_per_term=8):
    print(f"===== {path}")
    doc = fitz.open(path)
    print(f"[pages={doc.page_count}]")
    full = []
    for p in doc:
        full.append(p.get_text())
    text = "\n".join(full)
    norm = re.sub(r'\s+', ' ', text)
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
        (r"E:\work\Контроль\Проект_приводы\Конкуренты_каталоги\AUMA\Каталог_технический_AUMA_SA.pdf",
         ["RWG", "EWG", "MWG", "WSR", "DSR", "TSR", "DÖL", "WÖL", "DOL", "WOL"]),
        (r"E:\work\Контроль\Проект_приводы\Конкуренты_каталоги\AUMA\РАСШИФРОВКА СХЕМ АУМА.pdf",
         ["RWG", "EWG", "MWG", "WSR", "DSR", "TSR", "DÖL", "WÖL", "кОм", "potentiometer"]),
    ]:
        try:
            probe(path, terms)
        except Exception as e:
            print(f"ERROR {path}: {e}")
