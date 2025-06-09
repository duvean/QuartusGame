from abc import ABC, abstractmethod
from typing import List

from core.BehaviorModifiersRegister import register_modifier


class BehaviorModifier(ABC):
    @abstractmethod
    def apply(self, output_values: List[int]) -> List[int]:
        """
        Применяет модификатор к выходным значениям.
        """
        raise NotImplementedError

    def compute_outputs(self, input_values: List[int]) -> List[int]:
        """
        Расчитывает значения в цепи с модифицированными условиями.
        """
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> dict:
        """
        Возвращает сериализованный словарь, включая тип и параметры.
        """
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> 'BehaviorModifier':
        """
        Создает модификатор из сериализованного словаря.
        """
        pass


@register_modifier("Delay")
class DelayModifier(BehaviorModifier):
    def __init__(self):
        self.delay_ticks = 1
        self.tick_count = 0
        self.queue = []

    def set_params(self, delay_ticks: int):
        self.delay_ticks = delay_ticks

    def apply(self, output_values: List[int]) -> List[int]:
        self.queue.append(output_values[:])
        self.tick_count += 1

        if self.tick_count <= self.delay_ticks:
            return [0] * len(output_values)

        return self.queue.pop(0)

    def reset(self):
        self.tick_count = 0
        self.queue.clear()

    def to_dict(self):
        return {"delay_ticks": self.delay_ticks}

    @classmethod
    def from_dict(cls, data):
        instance = cls()
        instance.set_params(data.get("delay_ticks", 1))
        return instance