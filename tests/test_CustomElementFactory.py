import pytest
from core import CustomElementFactory, Grid, InputElement, OutputElement
from math import ceil

@pytest.fixture
def test_grid_dict():
    grid = Grid()
    input1 = InputElement()
    output1 = OutputElement()
    grid.add_element(input1, 0, 0)
    grid.add_element(output1, 10, 10)
    grid.connect_elements(input1, 0, output1, 0)
    return grid.to_dict()

def test_make_custom_element_class(test_grid_dict):
    name = "MyCustom"
    CustomClass = CustomElementFactory.make_custom_element_class(name, test_grid_dict)
    assert CustomClass.__name__ == name

    instance = CustomClass()
    assert instance.name == name
    assert instance.num_inputs == 1
    assert instance.num_outputs == 1
    assert isinstance(instance.input_names, list)
    assert isinstance(instance.output_names, list)
    assert "Input" in instance.input_names
    assert "Output" in instance.output_names
    assert isinstance(instance._subgrid, Grid)

def test_custom_element_compute_outputs(test_grid_dict):
    CustomClass = CustomElementFactory.make_custom_element_class("CustomTest", test_grid_dict)
    instance = CustomClass()

    instance.get_input_value = lambda i: 1
    for e in instance._subgrid.elements:
        if isinstance(e, OutputElement):
            e.get_input_value = lambda i: 1

    instance.compute_outputs()
    assert instance.output_values == [1]