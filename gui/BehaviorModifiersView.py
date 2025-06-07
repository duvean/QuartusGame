from PyQt6.QtWidgets import QWidget, QFormLayout, QSpinBox

from core.BehaviorModifiers import *
from core.BehaviorModifiersRegister import *


class ModifierEditor(QWidget):
    """Базовый интерфейс для UI-редакторов модификаторов"""
    def get_modifier(self) -> BehaviorModifier:
        raise NotImplementedError


@register_modifier_editor(DelayModifier)
class DelayModifierEditor(ModifierEditor):
    def __init__(self, modifier: DelayModifier, parent=None):
        super().__init__(parent)
        self.modifier = modifier
        layout = QFormLayout(self)
        self.spin = QSpinBox()
        self.spin.setRange(1, 100)
        self.spin.setValue(modifier.delay_ticks)
        layout.addRow("Задержка (ticks):", self.spin)

    def get_modifier(self) -> DelayModifier:
        self.modifier.set_params(self.spin.value())
        return self.modifier


class ModifierViewFactory:
    @staticmethod
    def create_modifier_editor(modifier: BehaviorModifier, parent=None) -> ModifierEditor:
        if isinstance(modifier, DelayModifier):
            return DelayModifierEditor(modifier, parent)
        # другие типы...
        return None




