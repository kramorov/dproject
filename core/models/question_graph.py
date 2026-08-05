"""QuestionGraph — граф вопросов-ответов для мастера подбора.

Каждый узел — вопрос с фильтрами и branching-логикой.
Рёбра — переходы между вопросами на основе ответов пользователя.
"""
from django.db import models
from core.models.equipment_type import EquipmentType
from core.models.base import BaseAbstractModel


class QuestionGraph(BaseAbstractModel):
    """Граф вопросов-ответов для пошагового подбора оборудования."""

    equipment_type = models.ForeignKey(
        EquipmentType,
        on_delete=models.CASCADE,
        related_name='question_graphs',
        verbose_name='Тип оборудования',
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Код графа',
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
    )
    graph_json = models.JSONField(
        default=dict,
        verbose_name='Граф (JSON)',
        help_text='Структура: {"entry_node": "...", "nodes": {...}, "edges": [...]}',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
    )

    class Meta:
        verbose_name = 'Граф вопросов-ответов'
        verbose_name_plural = 'Графы вопросов-ответов'
        ordering = ['code']

    def __str__(self):
        return self.name

    def get_node(self, node_id: str) -> dict | None:
        """Получить узел по ID."""
        return self.graph_json.get('nodes', {}).get(node_id)

    def get_entry_node(self) -> dict | None:
        """Получить начальный узел."""
        entry_id = self.graph_json.get('entry_node')
        if entry_id:
            return self.get_node(entry_id)
        return None

    def get_next_node(self, current_node_id: str, answer_value: str | None = None) -> dict | None:
        """
        Определить следующий узел на основе текущего узла и ответа.

        Если у узла есть branches — выбирает ветку по answer_value.
        Иначе идёт по edges графа.
        """
        node = self.get_node(current_node_id)
        if not node:
            return None

        # Проверяем branching
        branches = node.get('branches', {})
        if branches and answer_value is not None:
            next_id = branches.get(str(answer_value)) or branches.get('__default__')
            if next_id:
                return self.get_node(next_id)

        # Fallback: ищем ребро в edges
        edges = self.graph_json.get('edges', [])
        for edge in edges:
            if edge.get('from') == current_node_id:
                return self.get_node(edge['to'])

        return None

    def resolve_path(self, answers: dict[str, str]) -> list[str]:
        """
        Пройти граф с заданными ответами и вернуть список пройденных узлов.

        answers: {node_id: answer_value, ...}
        """
        path = []
        current_id = self.graph_json.get('entry_node')
        visited = set()

        while current_id and current_id not in visited:
            visited.add(current_id)
            path.append(current_id)

            answer = answers.get(current_id)
            current_id = self._get_next_node_id(current_id, answer)

        return path

    def _get_next_node_id(self, node_id: str, answer_value: str | None = None) -> str | None:
        """Вернуть ID следующего узла (без загрузки полного узла)."""
        node = self.graph_json.get('nodes', {}).get(node_id)
        if not node:
            return None

        branches = node.get('branches', {})
        if branches and answer_value is not None:
            return branches.get(str(answer_value)) or branches.get('__default__')

        for edge in self.graph_json.get('edges', []):
            if edge.get('from') == node_id:
                return edge['to']

        return None
