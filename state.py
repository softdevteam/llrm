
class State(object):
    ''' Represents the state of a stack frame or of the entire program. '''

    def __init__(self):
        self.vars = []
        self.var_offsets = {}

    def get_variable(self, name):
        ''' Returns the value of the specified local variable. '''
        off = self.get_variable_off(name)
        return self.vars[off]

    #@jit.elidable_promote()
    def get_variable_off(self, name):
        ''' Returns the offset of the specified local variable. '''
        off = self.var_offsets.get(name, -1)
        if off == -1:
            off = len(self.vars)
            self.var_offsets[name] = off
            self.vars.append(-1)
        return off

    def set_variable(self, name, val):
        ''' Sets the given local variable to a specified value. '''
        off = self.get_variable_off(name)
        self.vars[off] = val

    def has_key(self, name):
        ''' Checks if a given key exists in the dictionary. '''
        off = self.var_offsets.get(name, -1)
        if off == -1:
            return False
        return True
