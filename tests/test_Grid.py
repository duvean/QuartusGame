import pytest
from core import Grid, InputElement, OutputElement, AndElement, Level

@pytest.fixture
def grid():
    return Grid()

def test_add_element(grid):
    inp = InputElement()
    assert grid.add_element(inp, 0, 0) is True
    assert inp in grid.elements
    assert inp.position == (0, 0)

def test_add_element_conflict(grid):
    inp1 = InputElement()
    inp2 = InputElement()
    grid.add_element(inp1, 0, 0)
    assert grid.add_element(inp2, 0, 0) is False  # конфликт по позиции

def test_remove_element(grid):
    inp = InputElement()
    grid.add_element(inp, 0, 0)
    assert grid.remove_element(inp) is True
    assert inp not in grid.elements
    assert inp.position is None

def test_generate_unique_name(grid):
    name1 = grid.generate_unique_name("Input")
    name2 = grid.generate_unique_name("Input")
    assert name1 != name2
    assert name1.startswith("Input")
    assert name2.startswith("Input")

def test_create_element(grid):
    e = grid.create_element(InputElement)
    assert isinstance(e, InputElement)
    assert e.name in grid.existing_names

def test_get_element_at(grid):
    inp = InputElement()
    grid.add_element(inp, 1, 2)
    found = grid.get_element_at(1, 2)
    assert found == inp

def test_rename_element(grid):
    inp = InputElement()
    grid.add_element(inp, 0, 0)
    old_name = inp.name
    assert grid.rename_element(inp, "NewName")
    assert inp.name == "NewName"
    assert "NewName" in grid.existing_names
    assert old_name not in grid.existing_names

def test_move_element(grid):
    inp = InputElement()
    grid.add_element(inp, 0, 0)
    assert grid.move_element(inp, 3, 3) is True
    assert inp.position == (3, 3)

def test_move_element_conflict(grid):
    inp1 = InputElement()
    inp2 = InputElement()
    grid.add_element(inp1, 0, 0)
    grid.add_element(inp2, 3, 3)
    assert grid.move_element(inp2, 0, 0) is False

def test_is_valid_circuit(grid):
    inp = InputElement()
    out = OutputElement()
    grid.add_element(inp, 0, 0)
    grid.add_element(out, 10, 10)
    inp.connect_output(0, out, 0)
    assert grid.is_valid_circuit() is True

def test_invalid_circuit(grid):
    inp = InputElement()
    grid.add_element(inp, 0, 0)
    assert grid.is_valid_circuit() is False  # нет выходов

def test_auto_test_success(grid):
    inp = InputElement()
    out = OutputElement()
    and_gate = AndElement()

    inp.name = "A"
    out.name = "Q"
    and_gate.name = "G"

    grid.add_element(inp, 0, 0)
    grid.add_element(and_gate, 1, 0)
    grid.add_element(out, 2, 0)

    inp.connect_output(0, and_gate, 0)
    inp.connect_output(0, and_gate, 1)  # дважды один и тот же вход
    and_gate.connect_output(0, out, 0)


    input_names = ["A"]
    output_names = ["Q"]
    truth_table = {(0,): (0,), (1,): (1,)}
    level = Level(truth_table, input_names, output_names)
    grid.set_level(level)

    errors = grid.auto_test()
    assert errors == []

def test_auto_test_failure(grid):
    inp = InputElement()
    out = OutputElement()
    out.name = "Q"
    inp.name = "A"
    grid.add_element(inp, 0, 0)
    grid.add_element(out, 1, 0)
    inp.connect_output(0, out, 0)

    input_names = ["A"]
    output_names = ["Q"]
    truth_table = {(0,): (1,), (1,): (0,)}
    level = Level(truth_table, input_names, output_names)
    grid.set_level(level)

    errors = grid.auto_test()
    assert errors is not None