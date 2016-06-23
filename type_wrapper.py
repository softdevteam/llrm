
class Type(object):
    def __init__(self):
        self.value = None

class Integer(Type):
    def __init__(self, value):
        self.value = value

class Float(Type):
    def __init__(self, value):
        self.value = value

class String(Type):
    def __init__(self, value):
        self.value = value

# should contain wrapper types
class List(Type):
    def __init__(self, value):
        self.value = value

class Tuple(Type):
    def __init__(self, value):
        self.value = value

