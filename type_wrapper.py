class Type(object):
    pass

class NumericType(Type):
    pass

class CompositeType(Type):
    pass

class Float(NumericType):
    def __init__(self, value):
        self.value = value

class Integer(Float):
    def __init__(self, value):
        self.value = value

class String(Type):
    def __init__(self, value):
        self.value = value

# should contain wrapper types
class List(CompositeType):
    def __init__(self, value):
        self.value = value

class Tuple(CompositeType):
    def __init__(self, value):
        self.value = value

