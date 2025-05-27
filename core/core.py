from collections import deque, defaultdict
import itertools
from operator import truth
from typing import List

from .logic_elements import *

class Grid:
    def __init__(self):
        self.elements: List[LogicElement] = []
        self.occupied_cells: Set[Tuple[int, int]] = set()

    def get_occupied_cells(self) -> Set[Tuple[int, int]]:
        return set().union(*[elem.occupied_cells for elem in self.elements])

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

    def move_element(self, element, new_x: int, new_y: int) -> bool:
        if element not in self.elements:
            return False

        # Сохраняем оригинальные координаты
        original_x, original_y = element.position
        original_cells = element.occupied_cells

        # Временно удаляем элемент
        self.elements.remove(element)
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


class Level:
    def __init__(self, grid: Grid, truth_table: Dict[Tuple[int, ...], Tuple[int, ...]]):
        self.grid = grid
        self.truth_table = truth_table

    def get_input_elements(self) -> List[InputElement]:
        return [e for e in self.grid.elements if isinstance(e, InputElement)]

    def get_input_names(self) -> List[str]:
        return [e.name for e in self.grid.elements if isinstance(e, InputElement)]

    def get_output_elements(self) -> List[OutputElement]:
        return [e for e in self.grid.elements if isinstance(e, OutputElement)]

    def get_output_names(self) -> List[str]:
        return [e.name for e in self.grid.elements if isinstance(e, OutputElement)]

    def get_truth_table(self) -> Dict[Tuple[int, ...], Tuple[int, ...]]:
        return self.truth_table

    def is_valid_circuit(self) -> bool:
        return self.grid.is_valid_circuit()

    def compute_outputs(self, input_values: Dict[InputElement, int], max_iterations: int = 10) -> Optional[Dict[OutputElement, int]]:
        for inp, val in input_values.items():
            inp.set_value(val)

        output_elements = self.get_output_elements()
        previous_values = {out: None for out in output_elements}

        for _ in range(max_iterations):
            for element in self.grid.elements:
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

    def auto_test(self) -> List[Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]]]:
        input_elements = self.get_input_elements()
        output_elements = self.get_output_elements()
        errors = []

        for combo in itertools.product([0, 1], repeat=len(input_elements)):
            input_mapping = {inp: combo[i] for i, inp in enumerate(input_elements)}
            expected = self.truth_table.get(combo, None)

            if expected is None:
                continue

            actual = self.compute_outputs(input_mapping)
            if actual is None:
                # Цикл не стабилизировался
                errors.append((combo, expected, ("Cycle",)))
                continue

            actual_values = tuple(actual[out] for out in output_elements)
            if actual_values != expected:
                errors.append((combo, expected, actual_values))

        return errors


class GameModel:
    def __init__(self, level: Level):
        self.grid = level.grid
        self.current_level = level
        self.selected_element_type: Optional[type] = None
        self.toolbox: List[type] = [InputElement, OutputElement, AndElement, OrElement, XorElement, NotElement, CustomElement]
        self.name_counter = defaultdict(int)
        self.existing_names = set()

    def start_level(self, level_index: int):
        """Загружает указанный уровень"""
        if 0 <= level_index < len(self.levels):
            self.current_level = self.levels[level_index]
            self.grid = self.current_level.grid

    def create_element(self, element_type: type) -> Optional[LogicElement]:
        """Создает новый элемент (без размещения на поле)"""
        if element_type in self.toolbox:
            new_element = element_type()
            new_element.name = self.generate_unique_name(new_element.name)
            return new_element
        return None

    def generate_unique_name(self, base):
        while True:
            self.name_counter[base] += 1
            candidate = f"{base}_{self.name_counter[base]}"
            if candidate not in self.existing_names:
                self.existing_names.add(candidate)
                return candidate

    def rename_element(self, element: LogicElement, new_name: str) -> bool:
        if new_name in self.existing_names:
            return False
        self.existing_names.discard(element.name)
        element.name = new_name
        self.existing_names.add(new_name)
        return True

    def place_element(self, element: LogicElement, x: int, y: int) -> bool:
        """Пытается разместить элемент на поле"""
        return self.grid.add_element(element, x, y)

    def remove_element(self, element: LogicElement) -> bool:
        """Удаляет элемент с поля"""
        if self.grid.remove_element(element):
            self.existing_names.discard(element.name)
            return True
        return False

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
            return self.current_level.auto_test()
        return []

    def is_level_passed(self) -> bool:
        return self.current_level is not None \
            and self.current_level.is_valid_circuit() \
            and len(self.current_level.auto_test()) == 0

    def check_level(self) -> List[Tuple]:
        """
        Проверяет корректность схемы и прохождение уровня.

        Возвращает:
            - Пустой список, если схема корректна и проходит тест;
            - Список ошибок, если есть ошибки.
        """
        level = self.current_level
        if not level or not level.is_valid_circuit():
            return []

        errors = level.auto_test()
        return errors