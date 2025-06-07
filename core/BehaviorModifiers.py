from abc import ABC
from typing import List


class BehaviorModifier(ABC):
    def compute_next_state(self, element: 'LogicElement'):
        raise NotImplementedError

    def tick(self, element: 'LogicElement'):
        raise NotImplementedError


class DelayModifier(BehaviorModifier):
    def __init__(self, delay_ticks: int):
        self.delay_ticks = delay_ticks
        self.tick_count = 0
        self.queue = []

    def apply(self, output_values: List[int]) -> List[int]:
        self.queue.append(output_values[:])  # Копия выходных значений
        self.tick_count += 1

        if self.tick_count <= self.delay_ticks:
            return [0] * len(output_values)  # Пока не прошло достаточно тиков, выдаём нули

        return self.queue.pop(0)

    def reset(self):
        self.tick_count = 0
        self.queue.clear()