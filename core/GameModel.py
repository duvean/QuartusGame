import json
import os

from core.LogicElements import *
from core.Level import Level
from core.Grid import Grid
from core.CustomElementFactory import CustomElementFactory

USER_ELEMENTS_DIR = "user_elements"

class GameModel:
    def __init__(self, level: Level):
        self.grid = Grid()
        self.current_level = level
        self.selected_element_type: Optional[type] = None
        self.toolbox: List[type] = [InputElement, OutputElement, AndElement, OrElement, XorElement, NotElement,
                                    RSTriggerElement, DTriggerElement, SwitchingAndElement]
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
                    CustomClass = CustomElementFactory.make_custom_element_class(name, grid_data)
                    self.toolbox.append(CustomClass)
                except Exception as e:
                    print(f"Не удалось загрузить {filename}: {e}")

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