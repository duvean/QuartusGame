import json
import os

from core.LogicElements import *
from core.Level import Level
from core.Grid import Grid
from core.CustomElementFactory import CustomElementFactory
from core.LogicElementRegistry import ELEMENTS_REGISTRY

USER_ELEMENTS_DIR = "user_elements"

class GameModel:
    def __init__(self, level: Level):
        self.grid = Grid()
        self.load_user_elements()
        self.current_level = level
        self.toolbox: List[type] = list(ELEMENTS_REGISTRY.values())

    @staticmethod
    def load_user_elements():
        if not os.path.exists(USER_ELEMENTS_DIR):
            return

        for root, dirs, files in os.walk(USER_ELEMENTS_DIR):
            for filename in files:
                if filename.endswith(".json"):
                    path = os.path.join(root, filename)
                    with open(path, "r", encoding="utf-8") as f:
                        grid_data = json.load(f)

                    name = os.path.splitext(filename)[0]
                    try:
                        CustomClass = CustomElementFactory.make_custom_element_class(name, grid_data)
                        register_element(name, CustomClass, is_custom=True)
                    except Exception as e:
                        print(f"Не удалось загрузить {filename}: {e}")

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