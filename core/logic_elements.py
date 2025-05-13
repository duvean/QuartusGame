from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Set, Dict

class LogicElement(ABC):
    def __init__(
            self,
            num_inputs: int,
            num_outputs: int,
            width: int = 4,
            height: int = 3,
            name: str = "Element"
    ):
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.width = width
        self.height = height
        self.position: Optional[Tuple[int, int]] = None
        self.name = name

        self.input_connections: List[Optional[Tuple['LogicElement', int]]] = [
            None for _ in range(num_inputs)
        ]
        self.output_connections: List[List[Tuple['LogicElement', int]]] = [
            [] for _ in range(num_outputs)
        ]
        self.output_values: List[int] = [0] * num_outputs

    def get_output_values(self) -> List[int]:
        return self.output_values

    @property
    def occupied_cells(self) -> Set[Tuple[int, int]]:
        if self.position is None:
            return set()
        x, y = self.position
        return {
            (x + dx, y + dy)
            for dx in range(self.width)
            for dy in range(self.height)
        }

    def connect_output(self, output_port: int, target, target_input: int) -> bool:
        if output_port < 0 or output_port >= self.num_outputs:
            return False
        if target_input < 0 or target_input >= target.num_inputs:
            return False
        if not hasattr(self, "output_connections") or not isinstance(self.output_connections, list):
            return False
        if not hasattr(target, "input_connections") or not isinstance(target.input_connections, list):
            return False

        # Проверка на дублирование соединения
        for existing_target, existing_input in self.output_connections[output_port]:
            if existing_target is target and existing_input == target_input:
                return False

        self.output_connections[output_port].append((target, target_input))
        target.input_connections[target_input] = (self, output_port)
        print(f"Connected {output_port} with {target_input}")

        return True

    def disconnect_port(self, port_type, port_index):
        if port_type == "input":
            conn = self.input_connections[port_index]
            if conn is not None:
                source, source_output_index = conn
                source.output_connections[source_output_index] = [
                    (t, tp) for (t, tp) in source.output_connections[source_output_index]
                    if t != self or tp != port_index
                ]
            self.input_connections[port_index] = None

        elif port_type == "output":
            for target, target_port in self.output_connections[port_index]:
                if target.input_connections[target_port] == (self, port_index):
                    target.input_connections[target_port] = None
            self.output_connections[port_index].clear()

    def disconnect_all(self):
        for i in range(len(self.input_connections)):
            self.disconnect_port("input", i)
        for i in range(len(self.output_connections)):
            self.disconnect_port("output", i)

    def get_input_value(self, input_port: int) -> int:
        conn = self.input_connections[input_port]
        if conn:
            source_elem, source_port = conn
            value = source_elem.output_values[source_port]
            return value
        return 0

    @abstractmethod
    def compute_outputs(self):
        pass


class InputElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=0, num_outputs=1, name="Input")
        self.output_values[0] = 0

    def value(self):
        return self.output_values[0]

    def set_value(self, value: int):
        self.output_values[0] = value

    def compute_outputs(self):
        pass


class OutputElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=1, num_outputs=0, name="Output")
        self.value = 0

    def compute_outputs(self):
        self.value = self.get_input_value(0)


class AndElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=2, num_outputs=1, name="And")

    def compute_outputs(self):
        a = self.get_input_value(0)
        b = self.get_input_value(1)
        self.output_values[0] = a & b


class OrElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=2, num_outputs=1, name="Or")

    def compute_outputs(self):
        self.output_values[0] = 1 if (
            self.get_input_value(0) or self.get_input_value(1)
        ) else 0


class XorElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=2, num_outputs=1, name="Xor")

    def compute_outputs(self):
        self.output_values[0] = 0 if (
            self.get_input_value(0) == self.get_input_value(1)
        ) else 1


class NotElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=1, num_outputs=1, name="Not")

    def compute_outputs(self):
        self.output_values[0] = 1 if (
                self.get_input_value(0) == 0
        ) else 0