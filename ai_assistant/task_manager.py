"""Менеджер графа зависимостей задач подбора."""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Требования к каждому типу оборудования: обязательные и опциональные параметры.
# Каждая запись описывает:
# - label: человекочитаемое название типа оборудования.
# - required: список обязательных параметров — если хотя бы один отсутствует,
#   подбор не начинается, статус ``needs_info``.
# - optional: список опциональных параметров, уточняющих подбор.
# - depends_on: список типов оборудования, от которых зависит данный тип
#   (например, соленоид зависит от привода, т.к. размер резьбы берётся из
#   характеристик привода).
#
# Используется:
# - в DECOMPOSE_V2_PROMPT для перечисления обязательных параметров LLM.
# - в TaskGraph._execute_task для получения label при логировании.
# - на фронтенде / в фазе analyze для валидации полноты данных.
EQUIPMENT_REQUIREMENTS: Dict[str, dict] = {
    "actuator": {
        "label": "пневмопривод",
        "required": ["torque_nm"],
        "optional": [
            "valve_type", "dn", "pn", "actuator_variety", "safety_position",
            "air_pressure_bar", "safety_factor", "temperature_min", "temperature_max",
            "ip", "exd", "hand_wheel",
        ],
        "depends_on": [],
    },
    "solenoid": {
        "label": "соленоидный клапан",
        "required": ["voltage", "function_type"],
        "optional": ["connection_size", "body_material", "exd", "ip"],
        "depends_on": ["actuator"],
    },
    "bkv": {
        "label": "блок концевых выключателей",
        "required": [],
        "optional": ["exd", "ip", "inductive_sensors", "visual_indicator"],
        "depends_on": ["actuator"],
    },
    "cable_gland": {
        "label": "кабельный ввод",
        "required": [],
        "optional": ["exd", "armour_type", "cable_diameter"],
        "depends_on": ["solenoid", "bkv"],
    },
    "pneumatic_fitting": {
        "label": "пневматический фитинг",
        "required": [],
        "optional": ["connection_size"],
        "depends_on": ["solenoid", "actuator"],
    },
    "filter_regulator": {
        "label": "фильтр-регулятор",
        "required": [],
        "optional": ["air_pressure_bar", "connection_size"],
        "depends_on": [],
    },
    "manual_override": {
        "label": "ручной дублёр",
        "required": [],
        "optional": [],
        "depends_on": ["actuator"],
    },
}

# Промпт для фазы 1 (decompose). Передаётся в LLM вместе с system_prompt
# и текстом запроса пользователя. Описывает правила валидации, обязательные
# параметры каждого типа оборудования, формат ответа с секциями:
# === СТАТУС ===, === АНАЛИЗ ===, === ГЛОБАЛЬНЫЕ ТРЕБОВАНИЯ ===,
# === ЗАДАЧИ ===, === УТОЧНЕНИЯ ===, === ПРИЧИНА ОТКАЗА ===.
DECOMPOSE_V2_PROMPT = """{system_prompt}

Ты анализируешь запрос пользователя на подбор оборудования. Клиент хочет подобрать компоненты ДЛЯ СВОЕГО затвора/клапана (он УЖЕ есть у пользователя). Твоя задача — проверить полноту данных и составить план подбора КОМПОНЕНТОВ (пневмопривод, БКВ, соленоид, кабельные вводы, фитинги, фильтр-регулятор, ручной дублёр).

ПРАВИЛА:
1. Пользователь описывает свою арматуру (затвор, клапан) и хочет подобрать компоненты к ней.
2. Затвор/клапан сам по себе НЕ является задачей на подбор — он уже есть.
3. Некоторое оборудование зависит от другого (соленоид → размер резьбы привода).
4. Глобальные требования (температура, Exd, IP) применяются ко ВСЕМ компонентам.
5. Если для ОБЯЗАТЕЛЬНЫХ параметров какого-либо оборудования не хватает данных — НЕ начинай подбор. Статус: needs_info.
6. Если запрос НЕ относится к тематике арматуры и приводов — статус rejected.

ОБЯЗАТЕЛЬНЫЕ ПАРАМЕТРЫ ДЛЯ КАЖДОГО ТИПА ОБОРУДОВАНИЯ:
- пневмопривод (actuator): крутящий момент (torque_nm)
- соленоид (solenoid): напряжение питания (voltage), тип функции (function_type: 3/2, 5/2, 5/3)
- БКВ (bkv): обязательных нет
- кабельный ввод (cable_gland): обязательных нет
- фитинг (pneumatic_fitting): обязательных нет
- фильтр-регулятор (filter_regulator): обязательных нет
- ручной дублёр (manual_override): обязательных нет

ФОРМАТ ОТВЕТА (строго соблюдай структуру):

=== СТАТУС ===
ready | needs_info | rejected

=== АНАЛИЗ ===
(краткий текстовый анализ: что понял, какие компоненты нужны, что за арматура)

=== ГЛОБАЛЬНЫЕ ТРЕБОВАНИЯ ===
температура: (диапазон или отсутствует)
Exd: (категория или отсутствует)
IP: (степень или отсутствует)
давление в пневмосистеме: (бар или отсутствует)

=== ЗАДАЧИ ===
(только если статус ready. Каждая задача СТРОГО в формате:)
[id]: [тип_оборудования] | depends_on: [id,id] | [краткое описание, включая извлечённые параметры]

Примеры задач:
[1]: actuator | depends_on: [] | DA, 150Нм, ДУ300, IP65
[2]: bkv | depends_on: [1] | Exd II CT6
[3]: solenoid | depends_on: [1] | 24V DC, 5/2
[4]: cable_gland | depends_on: [2,3] | бронированный кабель

=== УТОЧНЕНИЯ ===
(только если статус needs_info. Конкретный список полей, которые нужно уточнить у пользователя)

=== ПРИЧИНА ОТКАЗА ===
(только если статус rejected. Кратко причину)

Запрос пользователя:
{user_text}"""


class TaskGraph:
    """Граф задач с топологической сортировкой и поуровневым выполнением.

    Принимает плоский список задач (из фазы analyze), строит DAG на основе
    ``depends_on``, вычисляет уровни через алгоритм Кана (Kahn's algorithm)
    и выполняет задачи уровень за уровнем, передавая результаты зависимых
    задач в последующие.

    Attributes:
        tasks: Словарь задач ``{task_id: task_dict}``.
        global_reqs: Глобальные требования, общие для всех задач.
        progress_log: Хронологический список шагов выполнения.
        results: Результаты завершённых задач ``{task_id: result_dict}``.
    """

    def __init__(self, tasks: List[dict], global_reqs: dict = None):
        """Создаёт граф задач.

        Args:
            tasks: Список словарей задач. Каждый словарь должен содержать
                ключи ``id`` и ``depends_on`` (список id зависимых задач).
            global_reqs: Глобальные требования (температура, Exd, IP, ...)
                или None.
        """
        self.tasks = {t["id"]: t for t in tasks}
        self.global_reqs = global_reqs or {}
        self.progress_log: List[dict] = []
        self.results: Dict[int, dict] = {}

    def sorted_levels(self) -> List[List[int]]:
        """Топологическая сортировка графа задач (алгоритм Кана).

        Вычисляет уровни DAG: задачи нулевого уровня не имеют зависимостей,
        задачи уровня N зависят только от задач уровней < N.

        Returns:
            Список уровней, где каждый уровень — список task_id, готовых
            к параллельному выполнению. Пример: ``[[1, 6], [2, 3], [4]]``.

        Note:
            При обнаружении циклической зависимости логирует ошибку
            и возвращает частичный результат (оставшиеся задачи
            игнорируются).
        """
        in_degree = {tid: len(t.get("depends_on", [])) for tid, t in self.tasks.items()}
        levels = []
        while in_degree:
            ready = [tid for tid, d in in_degree.items() if d == 0]
            if not ready:
                logger.error("Circular dependency in task graph")
                break
            levels.append(ready)
            for tid in ready:
                del in_degree[tid]
                for other_tid, other_t in self.tasks.items():
                    if tid in other_t.get("depends_on", []):
                        in_degree[other_tid] -= 1
        return levels

    def execute(self, orchestrator) -> List[dict]:
        """Выполняет граф задач по уровням.

        Для каждой задачи ищет метод ``_run_{type}_pipeline`` в оркестраторе,
        передаёт ему глобальные требования и результаты зависимых задач.

        Args:
            orchestrator: Экземпляр QueryOrchestrator, предоставляющий
                пайплайны для каждого типа оборудования.

        Returns:
            Список словарей progress_log с хронологией выполнения.
        """
        levels = self.sorted_levels()
        for level in levels:
            for task_id in level:
                self._execute_task(task_id, orchestrator)
        return self.progress_log

    def _execute_task(self, task_id: int, orchestrator):
        """Выполняет одну задачу: ищет обработчик, запускает, логирует.

        Порядок действий:
        1. Ищет в оркестраторе метод ``_run_{type}_pipeline``.
        2. Если обработчик не найден — помечает задачу как skipped.
        3. Собирает ``prev_results`` — результаты зависимых задач.
        4. Вызывает обработчик, сохраняет результат в ``self.results``.
        5. Логирует каждый шаг в ``self.progress_log``.

        Args:
            task_id: Идентификатор задачи.
            orchestrator: Экземпляр QueryOrchestrator с методами-пайплайнами.
        """
        task = self.tasks.get(task_id)
        if not task:
            return
        task_type = task.get("type", "")
        label = EQUIPMENT_REQUIREMENTS.get(task_type, {}).get("label", task_type)

        self.progress_log.append({"task_id": task_id, "status": "running",
                                  "message": f"Подбираю {label}..."})

        handler = getattr(orchestrator, f"_run_{task_type}_pipeline", None)
        if not handler:
            self.progress_log.append({"task_id": task_id, "status": "skipped",
                                      "message": f"{label} — нет схемы, поиск не выполнен"})
            self.results[task_id] = {"status": "skipped"}
            return

        try:
            prev_results = {tid: self.results[tid] for tid in task.get("depends_on", []) if tid in self.results}
            result = handler(task, self.global_reqs, prev_results)
            self.results[task_id] = result
            self.progress_log.append({"task_id": task_id, "status": result.get("status", "done"),
                                      "message": f"{label} — {result.get('message', 'Готово')}"})
        except Exception as e:
            logger.error(f"Task {task_id} ({task_type}) failed: {e}")
            self.progress_log.append({"task_id": task_id, "status": "error",
                                      "message": f"{label} — ошибка: {e}"})
            self.results[task_id] = {"status": "error", "message": str(e)}
