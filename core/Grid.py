import itertools
import re
from collections import deque, defaultdict

from core.LogicElements import *
from core.LogicElementRegistry import create_element_by_name
from core.Level import Level
from core.CustomElementFactory import CustomElementFactory
from core.BehaviorModifiers import *


class Grid:
    def __init__(self):
        self.level = None
        self.elements: List[LogicElement] = []
        self.occupied_cells: Set[Tuple[int, int]] = set()
        self.name_counter = defaultdict(int)
        self.existing_names = set()

    def set_level(self, level: Level) -> None:
        self.level = level

    def get_input_elements(self) -> List[InputElement]:
        return [e for e in self.elements if isinstance(e, InputElement)]

    def get_input_names(self) -> List[str]:
        return [e.name for e in self.elements if isinstance(e, InputElement)]

    def get_output_elements(self) -> List[OutputElement]:
        return [e for e in self.elements if isinstance(e, OutputElement)]

    def get_output_names(self) -> List[str]:
        return [e.name for e in self.elements if isinstance(e, OutputElement)]

    def get_occupied_cells(self) -> Set[Tuple[int, int]]:
        return set().union(*[elem.occupied_cells for elem in self.elements])

    def generate_unique_name(self, base: str) -> str:
        # Если base сам по себе свободен
        if base not in self.existing_names:
            self.existing_names.add(base)
            self.name_counter[base] = max(self.name_counter[base], 0)
            return base

        # Ищем свободное "base N"
        i = 1
        while True:
            candidate = f"{base} {i}"
            if candidate not in self.existing_names:
                self.existing_names.add(candidate)
                self.name_counter[base] = max(self.name_counter[base], i)
                return candidate
            i += 1

    def release_name(self, name: str):
        """ Освобождает имя, например при удалении элемента """
        self.existing_names.discard(name)

        # Опционально: уменьшаем name_counter если удаляем последний с таким индексом
        match = re.match(r"^(.*) (\d+)$", name)
        if match:
            base, num = match.group(1), int(match.group(2))
            if self.name_counter[base] == num:
                self.name_counter[base] -= 1

    def create_element(self, element_type: type) -> LogicElement:
        new_element = element_type()
        new_element.name = self.generate_unique_name(new_element.name)
        return new_element

    def add_element(self, element: LogicElement, x: int, y: int) -> bool:
        if element.position is not None:
            return False

        # Предварительный расчет клеток
        new_cells = {(x + dx, y + dy) for dx in range(element.width) for dy in range(element.height)}

        if any(self.get_occupied_cells() & new_cells):
            return False

        # Только теперь устанавливаем позицию
        element.position = (x, y)
        self.elements.append(element)
        return True

    @staticmethod
    def connect_elements(source: LogicElement, source_port: int,
                         target: LogicElement, target_port: int) -> bool:
        """Соединяет выход source с входом target"""
        return source.connect_output(source_port, target, target_port)

    @staticmethod
    def disconnect_port(source: LogicElement, port_type: str, port: int) -> bool:
        """Удаляет связи с выбранным портом"""
        return source.disconnect_port(port_type, port)

    def remove_element(self, element: LogicElement) -> bool:
        if element.position is not None:
            element.position = None
            self.release_name(element.name)
            self.elements.remove(element)
            return True
        return False

    def get_element_at(self, x: int, y: int) -> Optional[LogicElement]:
        for elem in self.elements:
            if elem.position is None:
                continue
            ex, ey = elem.position
            if (ex <= x < ex + elem.width and
                    ey <= y < ey + elem.height):
                return elem
        return None

    def rename_element(self, element: LogicElement, new_name: str) -> bool:
        if new_name in self.existing_names:
            return False
        self.existing_names.discard(element.name)
        #self.release_name(element.name)
        element.name = new_name
        self.existing_names.add(new_name)
        return True

    def move_element(self, element, new_x: int, new_y: int) -> bool:
        if element not in self.elements:
            return False

        # Сохраняем оригинальные координаты
        original_x, original_y = element.position
        original_cells = element.occupied_cells

        # Временно удаляем элемент
        self.elements.remove(element)
        self.occupied_cells = self.get_occupied_cells()
        self.occupied_cells -= original_cells

        # Пробуем новую позицию
        element.position = (new_x, new_y)
        new_cells = element.occupied_cells
        conflict = bool(new_cells & self.occupied_cells)

        if conflict:
            element.position = (original_x, original_y)
            self.elements.append(element)
            self.occupied_cells.update(original_cells)
            return False

        self.elements.append(element)
        self.occupied_cells.update(new_cells)
        return True

    def is_valid_circuit(self) -> bool:
        input_elements = [e for e in self.elements if isinstance(e, InputElement)]
        output_elements = [e for e in self.elements if isinstance(e, OutputElement)]

        if not input_elements or not output_elements:
            return False

        visited = set()
        queue = deque(input_elements)

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            for output_idx in range(current.num_outputs):
                for target, _ in current.output_connections[output_idx]:
                    if target not in visited:
                        queue.append(target)

        return all(out in visited for out in output_elements)

    def is_stable(self):
        for e in self.elements:
            if getattr(e, "is_sync", False):
                if e.output_values != getattr(e, "prev_output_values", []):
                    return False
        return True

    def tick_once(self):
        # Сначала комбинаторные
        for e in self.elements:
            if not getattr(e, 'is_sync', False):
                e.compute_outputs()

        # Затем — синхронные
        for e in self.elements:
            if getattr(e, 'is_sync', False):
                e.compute_next_state()
        for e in self.elements:
            if getattr(e, 'is_sync', False):
                e.tick()

    def compute_outputs(self, input_values: Dict[InputElement, int], max_iterations: int = 10):
        for inp, val in input_values.items():
            inp.set_value(val)

        # Разделение на типы
        stateless_elements = [e for e in self.elements if not getattr(e, 'is_sync', False)]
        stateful_elements = [e for e in self.elements if getattr(e, 'is_sync', False)]

        # 1. Сначала стабилизируем комбинаторную часть
        for _ in range(max_iterations):
            prev_outputs = [(e, list(e.output_values)) for e in stateless_elements]

            for e in stateless_elements:
                e.compute_outputs()

            if all(e.output_values == old for e, old in prev_outputs):
                break
        else:
            return None  # Комбинаторная часть не стабилизировалась

        # 2. Затем обрабатываем stateful-часть (триггеры и модификаторы)
        for _ in range(1): # max_iterations
            for e in stateful_elements:
                e.compute_next_state()
            for e in stateful_elements:
                e.tick()

            if self.is_stable():
                break
        else:
            return None  # Stateful часть не стабилизировалась

        return {out: out.value for out in self.get_output_elements()}

    def auto_test(self) -> List[Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...] | Tuple[str, ...]]]:
        if not self.level:
            return []

        input_elements_by_name = {e.name: e for e in self.get_input_elements()}
        output_elements_by_name = {e.name: e for e in self.get_output_elements()}

        try:
            input_elements = [input_elements_by_name[name] for name in self.level.input_names]
            output_elements = [output_elements_by_name[name] for name in self.level.output_names]
        except KeyError:
            return []

        # Сохраняем текущее состояние всех элементов (только выходы и внутренности)
        saved_states = {}
        for e in self.elements:
            saved_states[e] = {
                'outputs': list(e.output_values),
                'internal': getattr(e, 'save_state', lambda: None)()
            }

        errors = []

        for combo in itertools.product([0, 1], repeat=len(input_elements)):
            input_mapping = {inp: combo[i] for i, inp in enumerate(input_elements)}
            actual = self.compute_outputs(input_mapping)

            expected = self.level.truth_table.get(combo, None)
            print(f'Отладка: exp{expected}, act{actual}')
            if expected is None:
                continue

            if actual is None:
                errors.append((combo, expected, ("Cycle",)))
                continue

            actual_values = tuple(actual[out] for out in output_elements)
            if actual_values != expected:
                errors.append((combo, expected, actual_values))

        # Восстановление состояния
        for e in self.elements:
            e.output_values = list(saved_states[e]['outputs'])
            if 'internal' in saved_states[e]:
                restore = getattr(e, 'load_state', None)
                if callable(restore):
                    restore(saved_states[e]['internal'])

        return errors

    def to_dict(self):
        return {
            "elements": [e.to_dict() for e in self.elements],
            "connections": [
                {
                    "source": (self.elements.index(src), src_idx),
                    "target": (self.elements.index(trg), trg_idx)
                }
                for src in self.elements
                for src_idx, conns in enumerate(src.output_connections)
                for trg, trg_idx in conns
            ]
        }

    def load_from_dict(self, data):
        self.elements.clear()
        custom_classes = {}

        for elem_data in data["elements"]:
            elem_name = elem_data.get("name")
            elem_type = elem_data.get("type")
            subgrid_data = elem_data.get("subgrid")

            if subgrid_data:
                if elem_type not in custom_classes:
                    CustomClass = CustomElementFactory.make_custom_element_class(elem_type, subgrid_data)
                    custom_classes[elem_type] = CustomClass
                cls = custom_classes[elem_type]
                element = cls()
            else:
                cls = create_element_by_name(elem_type)
                if cls is None:
                    continue
                element = cls.from_dict(elem_data)

            self.elements.append(element)
            self.existing_names.add(elem_name)

        # Подключения
        for conn in data["connections"]:
            src_idx, src_port = conn["source"]
            trg_idx, trg_port = conn["target"]
            if src_idx < len(self.elements) and trg_idx < len(self.elements):
                self.elements[src_idx].connect_output(src_port, self.elements[trg_idx], trg_port)