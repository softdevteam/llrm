class Value(object):
    pass

class NumericValue(Value):
    pass

class CompositeValue(Value):
    pass

class Float(NumericValue):
    def __init__(self, value):
        self.value = value

class Integer(NumericValue):
    def __init__(self, value):
        self.value = value

class String(Value):
    def __init__(self, value):
        self.value = value

class List(CompositeValue):
    def __init__(self, value):
        self.value = value

class Tuple(CompositeValue):
    def __init__(self, value):
        self.value = value

class Ptr(Value):
    def __init__(self, value):
        self.value = value

class NoValue(Value):
    def __init__(self, value=None):
        self.value = value

class BasicBlock(Value):
    def __init__(self, value):
        self.value = value
