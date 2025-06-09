from abc import ABC, abstractmethod
from math import ceil
from typing import List, Tuple, Optional, Set, Dict

from core.BehaviorModifiers import *


class LogicElement(ABC):
    def __init__(
            self,
            num_inputs: int,
            num_outputs: int,
            width: int = 6,
            height: int = 4,
            name: str = "Element"
    ):
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.width = width
        self.height = ceil(max(num_inputs, num_outputs) * 1.5) + 1
        self.position: Optional[Tuple[int, int]] = None
        self.name = name
        self.is_sync = False

        # Модифицировано: теперь каждый вход может иметь несколько соединений
        self.input_connections: List[List[Tuple['LogicElement', int]]] = [
            [] for _ in range(num_inputs)
        ]
        self.output_connections: List[List[Tuple['LogicElement', int]]] = [
            [] for _ in range(num_outputs)
        ]
        self.output_values: List[int] = [0] * self.num_outputs
        self.next_output_values: List[int] = [0] * self.num_outputs

        self.input_names = [f"In{i + 1}" for i in range(num_inputs)]
        self.output_names = [f"Out{i + 1}" for i in range(num_outputs)]

        self._modifiers: List[BehaviorModifier] = []

    def add_modifier(self, modifier: BehaviorModifier):
        self._modifiers.append(modifier)

    def remove_modifier(self, modifier: BehaviorModifier):
        self._modifiers.remove(modifier)

    def clear_modifiers(self):
        self._modifiers.clear()

    @property
    def modifiers(self) -> List[BehaviorModifier]:
        return self._modifiers

    @modifiers.setter
    def modifiers(self, value: List[BehaviorModifier]):
        self._modifiers = value

    def apply_modifiers(self):
        for modifier in self._modifiers:
            self.output_values = modifier.apply(self.output_values)

    def get_input_port_name(self, index):
        return self.input_names[index] if index < len(self.input_names) else f"IN{index}"

    def set_input_port_name(self, index, name):
        if index < len(self.input_names):
            self.input_names[index] = name

    def get_output_port_name(self, index):
        return self.output_names[index] if index < len(self.output_names) else f"OUT{index}"

    def set_output_port_name(self, index, name):
        if index < len(self.output_names):
            self.output_names[index] = name

    def _hide_ports_names(self):
        self.input_names = ["" for i in range(self.num_inputs)]
        self.output_names = ["" for i in range(self.num_outputs)]

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
        target.input_connections[target_input].append((self, output_port))  # Модифицировано

        return True

    def disconnect_port(self, port_type, port_index):
        if port_type == "input":
            for source, source_output_index in self.input_connections[port_index]:
                source.output_connections[source_output_index] = [
                    (t, tp) for (t, tp) in source.output_connections[source_output_index]
                    if not (t is self and tp == port_index)
                ]
            self.input_connections[port_index].clear()

        elif port_type == "output":
            for target, target_port in self.output_connections[port_index]:
                target.input_connections[target_port] = [
                    (s, sp) for (s, sp) in target.input_connections[target_port]
                    if not (s is self and sp == port_index)
                ]
            self.output_connections[port_index].clear()

    def disconnect_all(self):
        for i in range(len(self.input_connections)):
            self.disconnect_port("input", i)
        for i in range(len(self.output_connections)):
            self.disconnect_port("output", i)

    def get_input_value(self, input_port: int) -> int:
        result = 0
        for source, source_output in self.input_connections[input_port]:
            if 0 <= source_output < len(source.output_values):
                if source.output_values[source_output]:
                    result = 1
                    break
        return result

    def compute_outputs(self):
        for modifier in self._modifiers:
            modifier.compute_next_state(self)

    def compute_next_state(self):
        for modifier in self._modifiers:
            modifier.compute_next_state(self)

    def tick(self):
        self.output_values = self.next_output_values[:]
        self.apply_modifiers()


class InputElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=0, num_outputs=1, name="Input")
        self._hide_ports_names()
        self.output_values[0] = 0
        self.height = 2
        self.width = 8

    def value(self):
        return self.output_values[0]

    def set_value(self, value: int):
        self.output_values[0] = value

    def compute_outputs(self):
        pass

    def tick(self):
        pass


class OutputElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=1, num_outputs=0, name="Output")
        self._hide_ports_names()
        self.value = 0
        self.height = 2
        self.width = 8

    def compute_outputs(self):
        self.value = self.get_input_value(0)


class AndElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=2, num_outputs=1, name="And")
        self._hide_ports_names()

    def compute_outputs(self):
        a = self.get_input_value(0)
        b = self.get_input_value(1)
        self.output_values[0] = a & b


class OrElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=2, num_outputs=1, name="Or")
        self._hide_ports_names()

    def compute_outputs(self):
        self.output_values[0] = 1 if (
            self.get_input_value(0) or self.get_input_value(1)
        ) else 0


class XorElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=2, num_outputs=1, name="Xor")
        self._hide_ports_names()

    def compute_outputs(self):
        self.output_values[0] = 0 if (
            self.get_input_value(0) == self.get_input_value(1)
        ) else 1


class NotElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=1, num_outputs=1, name="Not")
        self._hide_ports_names()

    def compute_outputs(self):
        self.output_values[0] = 1 if (
                self.get_input_value(0) == 0
        ) else 0


class RSTriggerElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=3, num_outputs=2, name="RSFF")
        self.is_sync = True
        self.state = 0
        self.input_names = ['R', 'S', 'clk']
        self.output_names = ['Q', 'Q̅']

    def compute_next_state(self):
        r = self.get_input_value(0)
        s = self.get_input_value(1)
        clk = self.get_input_value(2)

        if clk == 1:
            if s == 1 and r == 0:
                self._next_state = 1
            elif s == 0 and r == 1:
                self._next_state = 0
            elif s == 0 and r == 0:
                self._next_state = self.state
            else:
                # s == 1 and r == 1
                self._next_state = 0
        else:
            self._next_state = self.state

    def tick(self):
        self.state = getattr(self, "_next_state", self.state)
        self.next_output_values = [self.state, 1 - self.state]
        super().tick()


class DTriggerElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=2, num_outputs=2, name="DFF")  # D и CLK
        self.is_sync = True
        self.state = 0
        self.input_names = ['D', 'clk']
        self.output_names = ['Q', 'Q̅']
        #self.set_modifier(DelayModifier(delay_ticks=10))  # Задержка по желанию

    def compute_next_state(self):
        d = self.get_input_value(0)
        clk = self.get_input_value(1)
        if clk == 1:
            self._next_state = d
        else:
            self._next_state = self.state  # Не меняем состояние, если CLK == 0

    def tick(self):
        self.state = getattr(self, "_next_state", self.state)
        self.next_output_values = [self.state, 1 - self.state]
        super().tick()


class SwitchingAndElement(AndElement):
    def __init__(self):
        super().__init__()
        self.is_sync = True
        self.input_names = ['A', 'B']
        self.output_names = ['F']
        self.next_output_values = [0] * self.num_outputs
        self.add_modifier(SwitchAfterTicksModifier(ticks=60))

    def compute_next_state(self):
        super().compute_outputs()
        self.next_output_values = self.output_values[:]

    def tick(self):
        super().tick()





