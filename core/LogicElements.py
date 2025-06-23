import inspect
from abc import ABC, abstractmethod
from math import ceil
from typing import List, Tuple, Optional, Set, Dict

from PyQt6.QtCore import QTimer

from core.BehaviorModifiers import BehaviorModifier
from core.LogicElementRegistry import register_element
from core.BehaviorModifiersRegistry import MODIFIERS_REGISTRY, create_modifier_by_name

class Categorized:
    def __init__(self, category: str = "Прочее"):
        self.category = category

class LogicElement(Categorized, ABC):
    def __init__(
            self,
            num_inputs: int,
            num_outputs: int,
            width: int = 6,
            height: int = 4,
            name: str = "Element",
            category: str = "Прочее"
    ):
        super().__init__(category)
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.width = width
        self.height = max(self.num_inputs, self.num_outputs) + 2
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

    def to_dict(self):
        base = {
            "type": self.__class__.__name__,
            "name": self.name,
            "position": self.position,
            "input_names": self.input_names,
            "output_names": self.output_names,
            "modifiers": [
                {
                    "name": name,
                    "data": modifier.to_dict()
                }
                for modifier in self.modifiers
                for name, entry in MODIFIERS_REGISTRY.items()
                if isinstance(modifier, entry["class"])
            ]
        }

        # Получаем сигнатуру конструктора и добавляем нужные аргументы
        sig = inspect.signature(self.__init__)
        for param in sig.parameters.values():
            if param.name == "self":
                continue
            val = getattr(self, param.name, None)
            if val is not None:
                base[param.name] = val

        return base

    @classmethod
    def from_dict(cls, data):
        # Получаем сигнатуру конструктора
        sig = inspect.signature(cls.__init__)
        kwargs = {}

        # Извлекаем только параметры, которые явно указаны в сигнатуре
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            if name in data:
                kwargs[name] = data[name]
            elif param.default is not inspect.Parameter.empty:
                kwargs[name] = param.default
            else:
                raise ValueError(f"Отсутствуют аргументы конструктора: {name}")

        # Создание объекта с аргументами конструктора
        obj = cls(**kwargs)

        # Дополнительные параметры, не передаваемые в конструктор
        obj.name = data.get("name", obj.name)
        obj.position = tuple(data.get("position", (0, 0)))
        obj.input_names = data.get("input_names", obj.input_names)
        obj.output_names = data.get("output_names", obj.output_names)

        # Модификаторы
        for mod in data.get("modifiers", []):
            mod_name = mod.get("name")
            mod_data = mod.get("data", {})
            modifier = create_modifier_by_name(mod_name)
            if modifier and hasattr(modifier, "from_dict"):
                modifier = modifier.from_dict(mod_data) or modifier
            elif modifier:
                for k, v in mod_data.items():
                    setattr(modifier, k, v)
            if modifier:
                obj.add_modifier(modifier)

        return obj


@register_element(category="Вход-Выход")
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


@register_element(category="Вход-Выход")
class OutputElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=1, num_outputs=0, name="Output")
        self._hide_ports_names()
        self.value = 0
        self.height = 2
        self.width = 8

    def compute_outputs(self):
        self.value = self.get_input_value(0)


@register_element
class AndElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=2, num_outputs=1, name="And")
        self.height = 3
        self.width = 5
        self._hide_ports_names()

    def compute_outputs(self):
        a = self.get_input_value(0)
        b = self.get_input_value(1)
        self.output_values[0] = a & b


@register_element
class OrElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=2, num_outputs=1, name="Or")
        self.height = 3
        self.width = 5
        self._hide_ports_names()

    def compute_outputs(self):
        self.output_values[0] = 1 if (
            self.get_input_value(0) or self.get_input_value(1)
        ) else 0


@register_element
class XorElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=2, num_outputs=1, name="Xor")
        self.height = 3
        self.width = 5
        self._hide_ports_names()

    def compute_outputs(self):
        self.output_values[0] = 0 if (
            self.get_input_value(0) == self.get_input_value(1)
        ) else 1


@register_element
class NotElement(LogicElement):
    def __init__(self):
        super().__init__(num_inputs=1, num_outputs=1, name="Not")
        self.height = 3
        self.width = 5
        self._hide_ports_names()

    def compute_outputs(self):
        self.output_values[0] = 1 if (
                self.get_input_value(0) == 0
        ) else 0


@register_element
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


@register_element
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


@register_element(category="Вход-Выход")
class ClockGeneratorElement(LogicElement):
    def __init__(self, interval_ms=500):
        super().__init__(num_inputs=0, num_outputs=1, name="Clock")
        self._timer = QTimer()
        self._timer.timeout.connect(self._toggle_output)
        self.interval_ms = interval_ms
        self._state = 0

        self.width = 8
        self._hide_ports_names()

    def get_timer(self) -> QTimer:
        return self._timer

    def start(self):
        self._timer.start(self.interval_ms)

    def stop(self):
        self._timer.stop()

    def _toggle_output(self):
        self._state ^= 1
        self.output_values[0] = self._state
        self.next_output_values[0] = self._state
