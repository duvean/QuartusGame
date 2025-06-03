import pytest
from core.GameModel import *
from core.LogicElements import *


# -------------------- Фикстуры --------------------

@pytest.fixture
def basic_grid():
    grid = Grid()
    return grid


@pytest.fixture
def model():
    return GameModel()


# -------------------- GameModel --------------------

def test_game_model_create_and_test(model):
    a = InputElement()
    b = OutputElement()

    tt = {
        (0,): (0,),
        (1,): (1,),
    }
    level = Level(model.grid, tt)
    model.levels.append(level)
    model.start_level(1)

    model.place_element(a, 0, 0)
    model.place_element(b, 4, 4)
    model.connect_elements(a, 0, b, 0)

    model.run_auto_test()
    assert model.is_level_passed()


def test_game_model_duplicate_connection_raises(model):
    a = InputElement()
    b = OutputElement()
    model.place_element(a, 0, 0)
    model.place_element(b, 1, 1)
    model.connect_elements(a, 0, b, 0)
    assert not model.connect_elements(a, 0, b, 0)


def test_game_model_disconnected_input(model):
    a = InputElement()
    b = OutputElement()

    tt = {
        (0,): (0,),
        (1,): (1,),
    }
    level = Level(model.grid, tt)
    model.levels.append(level)
    model.start_level(1)

    model.place_element(a, 0, 0)
    model.place_element(b, 1, 1)  # b не подключён

    model.run_auto_test()
    assert not model.is_level_passed()


def test_game_model_change(model):
    a = InputElement()
    b = OutputElement()

    tt = {
        (0,): (0,),
        (1,): (1,),
    }
    level = Level(model.grid, tt)
    model.levels.append(level)
    model.start_level(1)

    model.place_element(a, 0, 0)
    model.place_element(b, 4, 4)
    model.connect_elements(a, 0, b, 0)

    model.run_auto_test()
    assert model.is_level_passed()

    # Изменим связь
    model.disconnect_port(a, "output", 0)
    model.run_auto_test()
    assert not model.is_level_passed()


def test_invalid_port_index():
    model = GameModel()
    a = model.create_element(InputElement)
    b = model.create_element(OutputElement)

    model.place_element(a, 0, 0)
    model.place_element(b, 4, 0)

    assert not model.connect_elements(a, 1, b, 0)  # нет 2-го выхода
    assert not model.connect_elements(a, 0, b, 1)  # нет 2-го входа


# -------------------- Level --------------------

def test_run_auto_test_with_full_truth_table():
    model = GameModel()
    a = InputElement()
    b = InputElement()
    and_gate = AndElement()
    q = OutputElement()

    # Подключение
    a.connect_output(0, and_gate, 0)
    b.connect_output(0, and_gate, 1)
    and_gate.connect_output(0, q, 0)

    # Расстановка
    model.grid.add_element(a, 0, 0)
    model.grid.add_element(b, 0, 1)
    model.grid.add_element(and_gate, 1, 0)
    model.grid.add_element(q, 2, 0)

    # Таблица истинности AND
    tt = {
        (0, 0): (0,),
        (0, 1): (0,),
        (1, 0): (0,),
        (1, 1): (1,)
    }

    model.level = Level(model.grid, tt)
    result = model.run_auto_test()
    assert result == []  # ошибок нет


def test_run_auto_test_with_errors(model):
    a = InputElement()
    q = OutputElement()

    # Подключение напрямую
    a.connect_output(0, q, 0)

    # Расстановка
    model.place_element(a, 0, 0)
    model.place_element(q, 1, 0)

    # Неверная таблица
    tt = {
        (0,): (1,),
        (1,): (0,)
    }

    model.levels.append(Level(model.grid, tt))
    model.start_level(1)
    result = model.run_auto_test()
    assert len(result) == 2  # обе строки неверны


def test_level_input_output_count(model):
    grid = Grid()
    grid.add_element(InputElement(), 0, 0)
    grid.add_element(OutputElement(), 4, 4)

    tt = {
        (0,): (0,),
        (1,): (1,)
    }
    model.levels.append(Level(grid, tt))
    model.start_level(1)

    assert len(model.current_level.get_input_elements()) == 1
    assert len(model.current_level.get_output_elements()) == 1


def test_level_without_inputs_or_outputs_raises(model):
    tt = {
        (0,): (0,),
        (1,): (1,)
    }
    level = Level(model.grid, tt)
    model.levels.append(level)
    model.start_level(1)
    assert not model.current_level.is_valid_circuit()


# -------------------- Проверка прохождения уровня --------------------

def test_level_passed_true(model):
    a = InputElement()
    q = OutputElement()

    tt = {
        (0,): (0,),
        (1,): (1,)
    }
    level = Level(model.grid, tt)
    model.levels.append(level)
    model.start_level(1)

    a.connect_output(0, q, 0)
    model.place_element(a, 0, 0)
    model.place_element(q, 4, 0)

    model.run_auto_test()
    assert model.is_level_passed()


def test_level_passed_false(model):
    a = InputElement()
    q = OutputElement()

    tt = {
        (0,): (1,),
        (1,): (0,)
    }
    level = Level(model.grid, tt)
    model.levels.append(level)
    model.start_level(1)

    a.connect_output(0, q, 0)
    model.place_element(a, 0, 0)
    model.place_element(q, 4, 0)

    model.run_auto_test()
    assert not model.is_level_passed()


# Grid

def test_add_and_get_element():
    grid = Grid()
    element = InputElement()
    grid.add_element(element, 1, 1)
    assert grid.get_element_at(1, 1) == element


def test_remove_element():
    grid = Grid()
    el = InputElement()
    grid.add_element(el, 2, 2)
    grid.remove_element(el)
    assert grid.get_element_at(2, 2) is None


def test_add_on_taken_place_raises():
    grid = Grid()
    el1 = InputElement()
    el2 = InputElement()
    grid.add_element(el1, 0, 0)
    assert not grid.add_element(el2, 0, 0)


def test_get_out_of_bounds_returns_none():
    grid = Grid()
    assert grid.get_element_at(-1, 100) is None
