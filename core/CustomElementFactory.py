from math import ceil

from core.LogicElements import LogicElement, OutputElement, InputElement
from core.Grid import Grid

class CustomElementFactory:
    @staticmethod
    def make_custom_element_class(class_name: str, grid_data: dict):
        class CustomElement(LogicElement):
            def __init__(self):
                subgrid = Grid()
                subgrid.load_from_dict(grid_data)

                # Сортируем входы и выходы по y для воспроизводимого порядка
                inputs = sorted(
                    [e for e in subgrid.elements if isinstance(e, InputElement)],
                    key=lambda el: el.position[1]
                )
                outputs = sorted(
                    [e for e in subgrid.elements if isinstance(e, OutputElement)],
                    key=lambda el: el.position[1]
                )

                input_count = len(inputs)
                output_count = len(outputs)

                super().__init__(
                    name=class_name,
                    num_inputs=input_count,
                    num_outputs=output_count,
                    height=ceil(max(input_count, output_count) * 1.5) + 1
                )

                self._subgrid = subgrid

                # Присваиваем имена портов из вложенной схемы
                self.input_names = [e.name for e in inputs]
                self.output_names = [e.name for e in outputs]

                # Флаг: нужна ли синхронная обработка
                self.is_sync = any(getattr(e, "is_sync", False) for e in self._subgrid.elements)

            def update_port_names_from_subgrid(self):
                inputs = sorted(
                    [e for e in self._subgrid.elements if isinstance(e, InputElement)],
                    key=lambda el: el.position[1]
                )
                outputs = sorted(
                    [e for e in self._subgrid.elements if isinstance(e, OutputElement)],
                    key=lambda el: el.position[1]
                )

                self.input_names = [e.name for e in inputs]
                self.output_names = [e.name for e in outputs]

            def _set_inputs(self):
                """Передаёт значения с внешних входов во внутреннюю схему"""
                input_index = 0
                for element in self._subgrid.elements:
                    if isinstance(element, InputElement):
                        element.set_value(self.get_input_value(input_index))
                        input_index += 1

            def _collect_outputs(self):
                """Собирает выходные значения из внутренних OutputElement"""
                output_values = []
                for element in self._subgrid.elements:
                    if isinstance(element, OutputElement):
                        val = element.get_input_value(0)
                        output_values.append(val)
                self.output_values = output_values

            def compute_outputs(self):
                """Используется в комбинаторной фазе"""
                if self.is_sync:
                    return  # Не считаем здесь, всё в tick()
                self._set_inputs()

                for _ in range(10):
                    prev = [list(e.output_values) for e in self._subgrid.elements if not getattr(e, 'is_sync', False)]
                    for e in self._subgrid.elements:
                        if not getattr(e, 'is_sync', False):
                            e.compute_outputs()
                    now = [list(e.output_values) for e in self._subgrid.elements if not getattr(e, 'is_sync', False)]
                    if prev == now:
                        break
                self._collect_outputs()

            def compute_next_state(self):
                """Для stateful-схем"""
                if not self.is_sync:
                    return
                self._set_inputs()
                for e in self._subgrid.elements:
                    e.compute_next_state()

            def tick(self):
                if not self.is_sync:
                    return
                for e in self._subgrid.elements:
                    e.tick()
                self._collect_outputs()

        CustomElement.__name__ = class_name
        return CustomElement