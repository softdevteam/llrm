from state import State
from type_wrapper import String
from type_wrapper import Integer
from type_wrapper import Float
from type_wrapper import Type

def test_set_var00():
    frame = State()
    assert frame.has_key(121) is False
    frame.set_variable(1234, String("testing"))
    assert frame.has_key(1234)
    assert frame.get_variable(1234).value == "testing"
    assert frame.get_variable_off(1234) == 0

def test_set_var01():
    frame = State()
    frame.set_variable(1345, Integer(20))
    assert frame.has_key(1345)
    assert frame.get_variable(1345).value == 20

    frame.set_variable(1345, String("something else"))
    assert frame.has_key(1345)
    assert frame.get_variable(1345).value == "something else"

    frame.set_variable(667, Float(2.78))
    assert frame.has_key(667)
    assert frame.get_variable(667).value == 2.78
    assert isinstance(frame.get_variable(667), Float)
    assert isinstance(frame.get_variable(667), Type)

def test_types01():
    frame = State()
    frame.set_variable(1345, Integer(20))
    frame.set_variable(15, String("something else"))
    frame.set_variable(667, Float(2.78))
    assert isinstance(frame.get_variable(1345), Integer)
    assert isinstance(frame.get_variable(1345), Type)
    assert isinstance(frame.get_variable(15), String)
    assert isinstance(frame.get_variable(15), Type)
    assert isinstance(frame.get_variable(667), Float)
    assert isinstance(frame.get_variable(667), Type)

