from core.logic_elements import *

def test_connect():
    inp = InputElement()
    out = OutputElement()
    inp.connect_output(0, out, 0)
    assert inp.output_connections[0] is not None
    assert out.input_connections[0] is not None

def test_disconnect():
    a = InputElement()
    b = AndElement()
    a.connect_output(0, b, 0)
    a.disconnect_all()
    assert b.input_connections[0] is None
    assert len(a.output_connections[0]) == 0

def test_input_element():
    inp = InputElement()
    inp.set_value(1)
    assert inp.get_output_values()[0] == 1
    inp.set_value(0)
    assert inp.get_output_values()[0] == 0

def test_output_element():
    inp = InputElement()
    inp.set_value(1)
    out = OutputElement()
    inp.connect_output(0, out, 0)
    out.compute_outputs()
    assert out.value == 1

def test_and_element():
    a, b, and_gate, out = InputElement(), InputElement(), AndElement(), OutputElement()
    a.set_value(1)
    b.set_value(1)
    a.connect_output(0, and_gate, 0)
    b.connect_output(0, and_gate, 1)
    and_gate.connect_output(0, out, 0)
    and_gate.compute_outputs()
    out.compute_outputs()
    assert and_gate.get_output_values()[0] == 1
    assert out.value == 1

def test_or_element():
    a, b, or_gate = InputElement(), InputElement(), OrElement()
    a.set_value(0)
    b.set_value(1)
    a.connect_output(0, or_gate, 0)
    b.connect_output(0, or_gate, 1)
    or_gate.compute_outputs()
    assert or_gate.get_output_values()[0] == 1

def test_xor_element():
    a, b, xor_gate = InputElement(), InputElement(), XorElement()
    a.set_value(1)
    b.set_value(0)
    a.connect_output(0, xor_gate, 0)
    b.connect_output(0, xor_gate, 1)
    xor_gate.compute_outputs()
    assert xor_gate.get_output_values()[0] == 1

    b.set_value(1)
    xor_gate.compute_outputs()
    assert xor_gate.get_output_values()[0] == 0

def test_not_element():
    a, not_gate = InputElement(), NotElement()
    a.set_value(0)
    a.connect_output(0, not_gate, 0)
    not_gate.compute_outputs()
    assert not_gate.get_output_values()[0] == 1

    a.set_value(1)
    not_gate.compute_outputs()
    assert not_gate.get_output_values()[0] == 0
