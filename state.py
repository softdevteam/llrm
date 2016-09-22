from type_wrapper import Integer, Value
from rpython.rlib import jit
from rpython.rtyper.lltypesystem import rffi

import llvm_wrapper as llwrap

class NoSuchVariableException(Exception):
    pass

class InterpreterState(object):

    def __init__(self, module=None, frame=None, global_state=None, last_block=None):
        self.update(module, frame, global_state, last_block)

    def update(self, module=None, frame=None, global_state=None, last_block=None):
        if module:
            self.module = module
        if frame:
            self.current_frame = frame
        if global_state:
            self.global_state = global_state
        if last_block:
            self.last_block = last_block

    def lookup_var(self, var, ignore_err=False):
        ''' Returns the value of a variable. First checks if the Variable
            is a Constant; if it is not an LLVM constant, the
            local variable dictionary is checked, followed by the global
            variable dictionary. Raises a NoSuchVariableException if the
            variable is not found in the dictionary and ignore_err=False.
            Returns None if the variable is not found and ignore_err=True.'''

        from llvm_objects import Constant
        if isinstance(var, Constant):
            return var.content
        elif self.current_frame.has_key(var.addr):
            return self.current_frame.get_variable(var.addr)
        elif self.global_state.has_key(var.addr):
            return self.global_state.get_variable(var.addr)
        elif not ignore_err:
            print "[ERROR]: Unknown variable. Exiting."
            error_str = rffi.charp2str(llwrap.LLVMPrintValueToString(var.l_value))
            raise NoSuchVariableException(error_str)

    def set_var(self, var, new_value):
        ''' Changes the value of an existing variable to the one specified. '''

        assert isinstance(new_value, Value)
        addr = rffi.cast(rffi.INT, var)
        if self.current_frame.has_key(addr):
            self.current_frame.set_variable(addr, new_value)
        elif self.global_state.has_key(addr):
            self.global_state.set_variable(addr, new_value)
        else:
            print "[ERROR]: Unknown variable. Exiting."
            error_str = rffi.charp2str(llwrap.LLVMPrintValueToString(var))
            raise NoSuchVariableException(error_str)

class State(object):
    ''' Represents the state of a stack frame or of the entire program. '''

    def __init__(self):
        self.vars = []
        self.var_offsets = {}

    def get_variable(self, name):
        ''' Returns the value of the specified local variable. '''

        off = self.get_variable_off(name)
        return self.vars[off]

    @jit.elidable_promote()
    def get_variable_off(self, name):
        ''' Returns the offset of the specified local variable. '''

        off = self.var_offsets.get(name, -1)
        if off == -1:
            off = len(self.vars)
            self.var_offsets[name] = off
            self.vars.append(Integer(-1))
        return off

    def set_variable(self, name, val):
        ''' Sets the given local variable to a specified value. '''

        off = self.get_variable_off(name)
        assert isinstance(val, Value)
        self.vars[off] = val

    def has_key(self, name):
        ''' Checks if a given key exists in the dictionary. '''

        off = self.var_offsets.get(name, -1)
        return off != -1
