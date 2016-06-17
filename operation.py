from llvm_wrapper import *
from rpython.rtyper.lltypesystem import rffi, lltype

class Operation(object):
    ''' A class to represent an operation '''
    not_set = True

    def __init__(self, opcode, args = []):
        self.opcode = opcode
        self.args = args

    def __eq__(self, other):
        return self.ref == other.ref
    def __eq__(self, other):
        return isinstance(other, Operation) and self.opcode == other.opcode \
                and self.args == other.args

    def __str__(self):
        return str(opcode)

    # only works for integers
    def _get_args(self, state):
        ''' Returns a list of arguments represented as integers '''
        arg_vals = []
        for arg in self.args:
            if LLVMIsConstant(arg):
                arg_vals.append(LLVMConstIntGetSExtValue(arg))
            else:
                # XXX temporary dummy value for argc is 3
                if Operation.not_set and "argc" in rffi.charp2str(LLVMPrintValueToString(arg)):
                    state.set_variable(rffi.cast(rffi.INT, arg), 3)
                    Operation.not_set = False
                arg_vals.append(state.get_variable(rffi.cast(rffi.INT, arg)))
        return arg_vals

    class UnknownOpcodeException(Exception):
        pass

    def execute(self, state = None):
        if self.opcode == LLVMRet:
            return 0
        elif self.opcode == LLVMAdd:
            x, y = self._get_args(state)
            return x + y
        elif self.opcode == LLVMMul:
            x, y = self._get_args(state)
            return x * y
        elif self.opcode == LLVMCall:
            # XXX deal with function calls and branching
            print "*" * 20, rffi.charp2str(LLVMGetValueName(self.args[0])), \
                            rffi.charp2str(LLVMGetValueName(self.args[1])), \
                            rffi.charp2str(LLVMGetValueName(self.args[2]))
            #block = LLVMGetFirstBasicBlock(self.args[2])
        elif self.opcode == LLVMAlloca:
            pass
        elif self.opcode == LLVMStore:
            pass
        elif self.opcode == LLVMOr:
            x, y = self._get_args(state)
            return x | y
        elif self.opcode == LLVMLoad:
            pass
        elif self.opcode == LLVMShl:
            x, y = self._get_args(state)
            return x << y
        else:
            raise UnknownOpcodeException(opcode)
        return 0
