import itertools
import json
import os
from collections import deque, defaultdict
from operator import truth
from typing import List

from .logic_elements import *
from .custom_element_factory import make_custom_element_class

USER_ELEMENTS_DIR = "user_elements"

class Level:
    def __init__(self,
                 truth_table: Dict[Tuple[int, ...], Tuple[int, ...]],
                 input_names: List[str],
                 output_names: List[str]
                 ):
        self.truth_table = truth_table
        self.input_names = input_names
        self.output_names = output_names

    def get_truth_table(self) -> Dict[Tuple[int, ...], Tuple[int, ...]]:
        return self.truth_table


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

    def generate_unique_name(self, base):
        while True:
            self.name_counter[base] += 1
            candidate = f"{base}_{self.name_counter[base]}"
            if candidate not in self.existing_names:
                self.existing_names.add(candidate)
                return candidate

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

    def remove_element(self, element: LogicElement) -> bool:
        if element.position is not None:
            element.position = None
            self.existing_names.discard(element.name)
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

    def compute_outputs(self, input_values: Dict[InputElement, int], max_iterations: int = 10) -> Optional[Dict[OutputElement, int]]:
        for inp, val in input_values.items():
            inp.set_value(val)

        output_elements = self.get_output_elements()
        previous_values = {out: None for out in output_elements}

        for _ in range(max_iterations):
            for element in self.elements:
                element.compute_outputs()

            stable = True
            for out in output_elements:
                if out.value != previous_values[out]:
                    stable = False
                previous_values[out] = out.value

            if stable:
                break
        else:
            return None

        return {out: out.value for out in output_elements}

    def auto_test(self) -> List[Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...] | Tuple[str, ...]]]:
        if not self.level:
            return []

        input_elements_by_name = {e.name: e for e in self.get_input_elements()}
        output_elements_by_name = {e.name: e for e in self.get_output_elements()}

        try:
            input_elements = [input_elements_by_name[name] for name in self.level.input_names]
            output_elements = [output_elements_by_name[name] for name in self.level.output_names]
        except KeyError:
            # Не возвращаем ошибки — это обработает UI
            return []

        errors = []

        for combo in itertools.product([0, 1], repeat=len(input_elements)):
            input_mapping = {inp: combo[i] for i, inp in enumerate(input_elements)}
            expected = self.level.truth_table.get(combo, None)

            if expected is None:
                continue

            actual = self.compute_outputs(input_mapping)
            if actual is None:
                errors.append((combo, expected, ("Cycle",)))
                continue

            actual_values = tuple(actual[out] for out in output_elements)
            if actual_values != expected:
                errors.append((combo, expected, actual_values))

        return errors

    def to_dict(self):
        return {
            "elements": [
                {
                    "type": e.__class__.__name__,
                    "name": e.name,
                    "position": e.position,
                    "input_names": e.input_names,
                    "output_names": e.output_names,
                    "subgrid": e._subgrid.to_dict() if hasattr(e, "_subgrid") else None
                }
                for e in self.elements
            ],
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
        type_map = {
            "InputElement": InputElement,
            "OutputElement": OutputElement,
            "AndElement": AndElement,
            "OrElement": OrElement,
            "NotElement": NotElement,
            "XorElement": XorElement,
            # кастомные — добавим ниже
        }

        custom_classes = {}

        # 1. Загружаем элементы
        for elem_data in data["elements"]:
            elem_type = elem_data["type"]
            subgrid_data = elem_data.get("subgrid")

            if subgrid_data:
                # Создаём вложенный кастомный класс, если не существует
                if elem_type not in custom_classes:
                    CustomClass = make_custom_element_class(elem_type, subgrid_data)
                    type_map[elem_type] = CustomClass
                    custom_classes[elem_type] = CustomClass
                cls = custom_classes[elem_type]
            else:
                cls = type_map.get(elem_type)

            if not cls:
                continue

            element = cls()
            element.name = elem_data["name"]
            element.position = tuple(elem_data["position"])
            element.input_names = elem_data["input_names"]
            element.output_names = elem_data["output_names"]

            self.elements.append(element)

        # 2. Загружаем соединения
        for conn in data["connections"]:
            src_idx, src_port = conn["source"]
            trg_idx, trg_port = conn["target"]
            if src_idx < len(self.elements) and trg_idx < len(self.elements):
                self.elements[src_idx].connect_output(src_port, self.elements[trg_idx], trg_port)


class GameModel:
    def __init__(self, level: Level):
        self.grid = Grid()
        self.current_level = level
        self.selected_element_type: Optional[type] = None
        self.toolbox: List[type] = [InputElement, OutputElement, AndElement, OrElement, XorElement, NotElement]
        self.load_user_elements()

    def load_user_elements(self):
        if not os.path.exists(USER_ELEMENTS_DIR):
            return

        for filename in os.listdir(USER_ELEMENTS_DIR):
            if filename.endswith(".json"):
                path = os.path.join(USER_ELEMENTS_DIR, filename)
                with open(path, "r", encoding="utf-8") as f:
                    grid_data = json.load(f)

                name = os.path.splitext(filename)[0]
                try:
                    custom_class = make_custom_element_class(name, grid_data)
                    self.toolbox.append(custom_class)
                except Exception as e:
                    print(f"Не удалось загрузить {filename}: {e}")



    def place_element(self, element: LogicElement, x: int, y: int) -> bool:
        """Пытается разместить элемент на поле"""
        return self.grid.add_element(element, x, y)

    def get_element_at(self, x: int, y: int) -> Optional[LogicElement]:
        """Возвращает элемент в указанной позиции"""
        return self.grid.get_element_at(x, y)

    def get_occupied_cells(self) -> Set[Tuple[int, int]]:
        """Возвращает занятые ячейки"""
        return self.grid.get_occupied_cells()

    @staticmethod
    def connect_elements(source: LogicElement, source_port: int,
                         target: LogicElement, target_port: int) -> bool:
        """Соединяет выход source с входом target"""
        return source.connect_output(source_port, target, target_port)

    @staticmethod
    def disconnect_port(source: LogicElement, port_type: str, port: int) -> bool:
        """Удаляет связи с выбранным портом"""
        return source.disconnect_port(port_type, port)

    def run_auto_test(self) -> List[Tuple]:
        """Запускает автоматическое тестирование схемы"""
        if self.current_level:
            return self.grid.auto_test()
        return []

    def is_level_passed(self) -> bool:
        return self.current_level is not None \
            and self.grid.is_valid_circuit() \
            and len(self.grid.auto_test()) == 0

    def check_level(self) -> List[Tuple]:
        """
        Проверяет корректность схемы и прохождение уровня.

        Возвращает:
            - Пустой список, если схема корректна и проходит тест;
            - Список ошибок, если есть ошибки.
        """
        if not self.current_level or not self.grid.is_valid_circuit():
            return []

        errors = self.grid.auto_test()
        return errors