from math import ceil

from .logic_elements import LogicElement

def make_custom_element_class(class_name: str, grid_data: dict):
    from .core import Grid
    class CustomElement(LogicElement):
        def __init__(self):
            # Определим количество входов и выходов по числу Input/OutputElement
            subgrid = Grid(None)
            subgrid.load_from_dict(grid_data)

            input_count = sum(1 for e in subgrid.elements if e.__class__.__name__ == "InputElement")
            output_count = sum(1 for e in subgrid.elements if e.__class__.__name__ == "OutputElement")

            super().__init__(
                name=class_name,
                num_inputs=input_count,
                num_outputs=output_count,
                height=ceil(max(input_count, output_count)*1.5)+1
                )
            self._subgrid = subgrid

        def compute_outputs(self):
            # Устанавливаем значения входов
            input_index = 0
            for element in self._subgrid.elements:
                if element.__class__.__name__ == "InputElement":
                    element.output_values[0] = self.get_input_value(input_index)
                    input_index += 1

            # Обновляем значения во всей вложенной схеме
            for element in self._subgrid.elements:
                element.compute_outputs()

            # Сохраняем выходы
            output_values = []
            for element in self._subgrid.elements:
                if element.__class__.__name__ == "OutputElement":
                    val = element.get_input_value(0)
                    output_values.append(val)
            self.output_values = output_values

    CustomElement.__name__ = class_name
    return CustomElement