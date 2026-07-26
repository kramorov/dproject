"""
Прогон sample-запросов через конвейер ai_assistant.
Показывает СЫРОЙ вывод каждой фазы в читаемом виде.

Запуск: python run_sample_pipeline.py [sample_id]
"""
import os, sys, json, traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
sys.path.insert(0, os.path.dirname(__file__))
import django; django.setup()

from ai_assistant.models import AIQuerySample, AIConversation, AIMessage, SelectionNode
from ai_assistant.services.tree_processor import TreeProcessor


def hr(title=""):
    print(f"\n{'─'*60}")
    if title:
        print(f"  {title}")
        print(f"{'─'*60}")


def run_sample(sample_id: int):
    sample = AIQuerySample.objects.get(id=sample_id)
    print(f"\n{'='*70}")
    print(f"СЭМПЛ #{sample.id}")
    print(f"{'='*70}")
    print(f"Текст: {sample.text.strip()[:300]}")

    # ── Фаза 1: Decompose ──
    hr("ФАЗА 1: DECOMPOSE")
    conv = AIConversation.objects.create(status="processing")
    tp = TreeProcessor(conv)

    print(f"Conversation: #{conv.id}")
    try:
        result = tp.decompose(sample.text)
    except Exception as e:
        print(f"DECOMPOSE УПАЛ: {e}")
        traceback.print_exc()
        # Покажем что успело записаться
        msgs = AIMessage.objects.filter(conversation=conv).order_by("id")
        for m in msgs:
            print(f"\n  Сообщение [{m.role}] intent={m.intent}:")
            print(f"  {m.content[:800]}")
        return

    print(f"  Статус: {result.get('status')}")
    if result.get('message'):
        print(f"  Сообщение: {result['message']}")

    # Покажем AIMessage (сырой ответ LLM)
    msgs = AIMessage.objects.filter(conversation=conv).order_by("id")
    for m in msgs:
        print(f"\n  ── [{m.role}] intent={m.intent} ──")
        content = m.content or "(пусто)"
        print(content[:2000])

    # Покажем дерево
    tree = result.get("tree", [])
    if tree:
        print(f"\n  Дерево ({len(tree)} позиций):")
        print(json.dumps(tree, ensure_ascii=False, indent=2)[:2000])

    # ── Фаза 2: Extract ──
    hr("ФАЗА 2: EXTRACT")
    nodes = list(conv.selection_nodes.all().order_by("level", "order"))
    if not nodes:
        print("  Нет узлов — extract невозможен.")
        return

    for node in nodes:
        label = node.label or "без названия"
        eq_code = node.equipment_type.code if node.equipment_type else "—"
        print(f"\n  Узел #{node.id} «{label}» (тип: {eq_code})")
        if not node.equipment_type:
            print("    Пропущен: нет типа оборудования")
            continue
        try:
            ext = tp.extract(node.id)
            print(f"    Статус: {ext.get('status')}")
            output = ext.get('extract_output')
            if output:
                print(f"    Фильтры: {json.dumps(output, ensure_ascii=False, indent=4)[:800]}")
            else:
                print(f"    Ответ: {json.dumps(ext, ensure_ascii=False, indent=2)[:500]}")
        except Exception as e:
            print(f"    ОШИБКА: {e}")
            traceback.print_exc()

        # Сырой ответ extract
        extract_msgs = AIMessage.objects.filter(
            conversation=conv, intent="extract"
        ).order_by("-id")[:1]
        for em in extract_msgs:
            print(f"\n    ── сырой ответ LLM (extract) ──")
            print(em.content[:1500])

        break  # только первый узел

    # ── Фаза 3: Filter ──
    hr("ФАЗА 3: FILTER")
    for node in nodes:
        if not node.equipment_type or not node.extract_output:
            continue
        endpoint = node.equipment_type.filter_endpoint or "нет endpoint"
        print(f"\n  Узел #{node.id} → {endpoint}")
        try:
            flt = tp.filter_node(node.id)
            print(f"    Статус: {flt.get('status')}")
            total = flt.get('total', 0)
            print(f"    Найдено вариантов: {total}")
            options = flt.get('options', [])
            if options:
                print(f"    Первые 3 варианта:")
                for o in options[:3]:
                    print(f"      {json.dumps(o, ensure_ascii=False)[:200]}")
        except Exception as e:
            print(f"    ОШИБКА: {e}")
            traceback.print_exc()
        break

    print(f"\n{'='*70}")
    print(f"ГОТОВО. Conversation #{conv.id}")
    print(f"{'='*70}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("sample_id", nargs="?", type=int, default=1, help="ID сэмпла (1-8)")
    p.add_argument("--all", action="store_true", help="Все 8")
    args = p.parse_args()

    ids = range(1, 9) if args.all else [args.sample_id]
    for sid in ids:
        try:
            run_sample(sid)
        except Exception as e:
            print(f"СЭМПЛ #{sid} УПАЛ: {e}")
            traceback.print_exc()
