import pytest
from unittest.mock import MagicMock, patch
from core import GameModel, Grid, InputElement, OutputElement, AndElement, Level

@pytest.fixture
def dummy_level():
    return Level("Test", [], [])

@pytest.fixture
def model(dummy_level):
    return GameModel(dummy_level)

def test_initial_state(model):
    assert isinstance(model.grid, Grid)
    assert model.current_level.name == "Уровень"
    assert not model._is_simulating
    assert model.selected_element_type is None
    assert InputElement in model.toolbox
    assert AndElement in model.toolbox

def test_run_auto_test_calls_grid(model):
    model.grid.auto_test = MagicMock(return_value=[(0, 1)])
    result = model.run_auto_test()
    model.grid.auto_test.assert_called_once()
    assert result == [(0, 1)]

def test_is_level_passed_valid(model):
    model.grid.is_valid_circuit = MagicMock(return_value=True)
    model.grid.auto_test = MagicMock(return_value=[])
    assert model.is_level_passed()

def test_check_level_invalid_circuit(model):
    model.grid.is_valid_circuit = MagicMock(return_value=False)
    assert model.check_level() == []

def test_check_level_returns_errors(model):
    model.grid.is_valid_circuit = MagicMock(return_value=True)
    model.grid.auto_test = MagicMock(return_value=[(1, 0)])
    assert model.check_level() == [(1, 0)]

def test_simulation_start_stop(model):
    model.frequency_input = MagicMock()
    model.frequency_input.value.return_value = 123

    model.start_simulation()
    assert model._is_simulating
    model.timer.isActive()  # Проверяется вручную

    model.stop_simulation()
    assert not model._is_simulating