"""Тест пайплайна: Phase 1 (decompose) + Phase 2 (extract) на семплах из БД."""

import json
import sys
from django.core.management.base import BaseCommand
from ai_assistant.models import AIConversation, AIQuerySample, SelectionNode
from ai_assistant.services.tree_processor import TreeProcessor


class Command(BaseCommand):
    help = "Прогоняет семплы запросов через decompose + extract и выводит таблицу"

    def add_arguments(self, parser):
        parser.add_argument("--sample-ids", nargs="*", type=int, help="IDs семплов (если не указано — все valid)")
        parser.add_argument("--max-nodes", type=int, default=5, help="Макс. узлов для extract на семпл")

    def handle(self, *args, **options):
        sample_ids = options.get("sample_ids")
        max_nodes = options["max_nodes"]

        if sample_ids:
            samples = AIQuerySample.objects.filter(id__in=sample_ids)
        else:
            samples = AIQuerySample.objects.filter(is_valid=True)

        if not samples:
            self.stdout.write(self.style.WARNING("No samples found"))
            return

        results = []
        for sample in samples:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Sample #{sample.id}: {sample.text[:100]}...")

            row = {
                "id": sample.id,
                "query": sample.text,
                "phase1_status": "error",
                "phase1_tree": None,
                "phase2_results": [],
            }

            try:
                # Phase 1: decompose
                conv = AIConversation.objects.create(status=AIConversation.PROCESSING)
                processor = TreeProcessor(conv)
                result1 = processor.decompose(text=sample.text)
                row["phase1_status"] = result1.get("status", "?")
                row["phase1_tree"] = result1.get("tree", {})

                self.stdout.write(f"  Phase 1: {row['phase1_status']}")

                if result1.get("status") == "error":
                    row["phase2_results"].append({"error": result1.get("message", "decompose failed")})
                else:
                    # Phase 2: extract for first N nodes
                    nodes = conv.selection_nodes.filter(
                        status="decomposed", equipment_type__isnull=False
                    )[:max_nodes]

                    for node in nodes:
                        self.stdout.write(f"  Extract node #{node.id} [{node.equipment_type.code}]...")
                        try:
                            result2 = processor.extract(node_id=node.id)
                            node.refresh_from_db()
                            row["phase2_results"].append({
                                "node_id": node.id,
                                "type": node.equipment_type.code,
                                "label": node.label,
                                "status": result2.get("status"),
                                "extract_output": node.extract_output,
                            })
                            self.stdout.write(f"    → {result2.get('status')}")
                        except Exception as e:
                            row["phase2_results"].append({
                                "node_id": node.id,
                                "type": node.equipment_type.code,
                                "error": str(e),
                            })
                            self.stdout.write(f"    → ERROR: {e}")

            except Exception as e:
                row["phase1_status"] = f"error: {e}"
                self.stdout.write(f"  Phase 1 ERROR: {e}")

            results.append(row)

        # Output table
        self._print_table(results)

    def _print_table(self, results):
        self.stdout.write("\n\n" + "=" * 80)
        self.stdout.write("РЕЗУЛЬТАТЫ ПРОГОНА ПАЙПЛАЙНА")
        self.stdout.write("=" * 80)

        for r in results:
            self.stdout.write(f"\n{'─'*80}")
            self.stdout.write(f"[{r['id']}] {r['query'][:120]}")
            self.stdout.write(f"  Phase 1: {r['phase1_status']}")

            if r["phase1_tree"]:
                pos = r["phase1_tree"].get("positions", [])
                self.stdout.write(f"  Позиций в дереве: {len(pos)}")
                if pos:
                    self.stdout.write(f"  Описание позиции: {pos[0].get('description', '?')[:100]}")

            for p2 in r["phase2_results"]:
                status = p2.get("status", p2.get("error", "?"))
                node_type = p2.get("type", "?")
                label = p2.get("label", "")[:60]
                self.stdout.write(f"  Phase 2 [{node_type}] {label}: {status}")

                if p2.get("extract_output"):
                    output = p2["extract_output"]
                    if isinstance(output, dict):
                        # Show key extracted values
                        show = {k: v for k, v in output.items() if v is not None and v != ""}
                        if show:
                            self.stdout.write(f"    Извлечено: {json.dumps(show, ensure_ascii=False)[:200]}")

        # Summary
        self.stdout.write(f"\n{'='*80}")
        total = len(results)
        p1_ok = sum(1 for r in results if r["phase1_status"] == "ready")
        p2_total = sum(len(r["phase2_results"]) for r in results)
        p2_ok = sum(
            1 for r in results for p2 in r["phase2_results"]
            if p2.get("status") in ("extracted",)
        )
        self.stdout.write(f"Итого: {total} семплов")
        self.stdout.write(f"  Phase 1 OK: {p1_ok}/{total}")
        self.stdout.write(f"  Phase 2 извлечений: {p2_ok}/{p2_total}")
