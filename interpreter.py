from __future__ import with_statement
from rpython.rlib import jit
from type_wrapper import String, Integer, Float, Ptr, List,\
                         Value, NoValue, NumericValue, BasicBlock
from llvm_wrapper import *
from state import State

import sys

def target(*args):
    return main, None

def jitpolicy(driver):
    from rpython.jit.codewriter.policy import JitPolicy
    return JitPolicy()

jit_driver = jit.JitDriver(greens=[], reds=[])

class NoSuchVariableException(Exception):
    pass

class NoSuchTypeException(Exception):
    pass

class InvalidFileException(Exception):
    pass

class UnparsableBitcodeException(Exception):
    pass

class Interpreter(object):

    def __init__(self, functions, global_state = None):
        self.functions = functions
        self.global_state = global_state

    def _get_args(self, args):
        ''' Returns a list of arguments. '''

        arg_vals = []
        for arg in args:
            arg_vals.append(self.lookup_var(arg))
        return arg_vals

    def exit_not_implemented(self, name):
        print "[ERROR]: Found unimplemented operation. Exiting."
        raise NotImplementedError(name)

    def puts(self, string, args=[]):
        print string
        if args:
            for arg in args:
                assert isinstance(arg, NumericValue)
                print arg.value
            print "\n\n"

    def lookup_var(self, var):
        ''' Returns the value of a variable. First checks locals, then globals. '''

        addr = rffi.cast(rffi.INT, var)
        if self.frame.has_key(addr):
            return self.frame.get_variable(addr)
        elif self.global_state.has_key(addr):
            return self.global_state.get_variable(addr)
        elif LLVMIsConstant(var):
            var_type = LLVMGetTypeKind(LLVMTypeOf(var))
            if var_type == LLVMIntegerTypeKind:
                return Integer(LLVMConstIntGetSExtValue(var))
            elif var_type == LLVMDoubleTypeKind or var_type == LLVMFloatTypeKind:
                with lltype.scoped_alloc(rffi.SIGNEDP.TO, 1) as signed_ptr:
                    return Float(LLVMConstRealGetDouble(var, signed_ptr))
            else:
                print "[ERROR]: Unknown type. Exiting."
                raise NoSuchTypeException(rffi.charp2str(LLVMPrintTypeToString(LLVMTypeOf(var))))
        else:
            print "[ERROR]: Unknown variable. Exiting."
            raise NoSuchVariableException(rffi.charp2str(LLVMPrintValueToString(var)))
        return NoValue()

    def get_phi_result(self, instruction):
        ''' Returns the result of a given phi instruction. '''
        for i in range(LLVMCountIncoming(instruction)):
            block = LLVMGetIncomingBlock(instruction, i)
            if block == self.last_block:
                return self.lookup_var(LLVMGetIncomingValue(instruction, i))

    def get_switch_block(self, args):
        ''' Returns the block a switch instruction branches to. '''

        cond = self.lookup_var(args[0])
        default_branch = args[1]
        assert isinstance(cond, Integer)
        for i in range(2, len(args), 2):
            switch_var = self.lookup_var(args[i])
            assert isinstance(switch_var, Integer)
            if cond.value == switch_var.value:
                return BasicBlock(args[i + 1])
        return BasicBlock(default_branch)

    def set_var(self, var, new_value):
        ''' Changes the value of an existing variable. '''

        assert isinstance(new_value, Value)
        addr = rffi.cast(rffi.INT, var)
        if self.frame.has_key(addr):
            self.frame.set_variable(addr, new_value)
        elif self.global_state.has_key(addr):
            self.global_state.set_variable(addr, new_value)
        else:
            print "[ERROR]: Unknown variable. Exiting."
            raise NoSuchVariableException(rffi.charp2str(LLVMPrintValueToString(var)))

    def has_function(self, function):
        ''' Return true if the file being interpreted contains a given function,
            false otherwise. '''

        if rffi.cast(rffi.INT, function) in self.functions:
            return True
        return False

    def eval_condition(self, predicate, val1, val2):
        ''' Returns the wrapped boolean result of the comparison of the values of
            the two arguments, according to an ICmp predicate. '''

        assert isinstance(val1, Integer) and isinstance(val2, Integer)
        if predicate == LLVMIntSLT:
            return Integer(val1.value < val2.value)
        elif predicate == LLVMIntSLE:
            return Integer(val1.value <= val2.value)
        elif predicate == LLVMIntEQ:
            return Integer(val1.value == val2.value)
        elif predicate == LLVMIntNE:
            return Integer(val1.value != val2.value)
        elif predicate == LLVMIntSGT:
            return Integer(val1.value > val2.value)
        elif predicate == LLVMIntSGE:
            return Integer(val1.value >= val2.value)
        else:
            self.exit_not_implemented("Unknown ICmp predicate %d" % predicate)

    def exec_operation(self, instruction):
        opcode = LLVMGetInstructionOpcode(instruction)
        args = [LLVMGetOperand(instruction, i)\
                for i in range(LLVMGetNumOperands(instruction))]
        if opcode == LLVMRet:
            if len(args) == 0:
                return NoValue()
            else:
                return self.lookup_var(args[0])
        elif opcode == LLVMAdd:
            x, y = self._get_args(args)
            assert isinstance(x, Integer) and isinstance(y, Integer)
            return Integer(x.value + y.value)
        elif opcode == LLVMFAdd:
            x, y = self._get_args(args)
            assert isinstance(x, Float) and isinstance(y, Float)
            return Float(x.value + y.value)
        elif opcode == LLVMMul:
            x, y = self._get_args(args)
            assert isinstance(x, Integer) and isinstance(y, Integer)
            return Integer(x.value * y.value)
        elif opcode == LLVMFMul:
            x, y = self._get_args(args)
            assert isinstance(x, Float) and isinstance(y, Float)
            return Float(x.value * y.value)
        elif opcode == LLVMSub:
            x, y = self._get_args(args)
            assert isinstance(x, Integer) and isinstance(y, Integer)
            return Integer(x.value - y.value)
        elif opcode == LLVMFSub:
            x, y = self._get_args(args)
            assert isinstance(x, Float) and isinstance(y, Float)
            return Float(x.value - y.value)
        elif opcode == LLVMSDiv:
            x, y = self._get_args(args)
            assert isinstance(x, Integer) and isinstance(y, Integer)
            return Integer(x.value / y.value)
        elif opcode == LLVMFDiv:
            x, y = self._get_args(args)
            assert isinstance(x, Float) and isinstance(y, Float)
            return Float(x.value / y.value)
        elif opcode == LLVMSRem:
            x, y = self._get_args(args)
            assert isinstance(x, Integer) and isinstance(y, Integer)
            return Integer(int(x.value) % int(y.value))
        elif opcode == LLVMAnd:
            x, y = self._get_args(args)
            assert isinstance(x, Integer) and isinstance(y, Integer)
            return Integer(int(x.value) & int(y.value))
        elif opcode == LLVMOr:
            x, y = self._get_args(args)
            assert isinstance(x, Integer) and isinstance(y, Integer)
            return Integer(int(x.value) | int(y.value))
        elif opcode == LLVMXor:
            x, y = self._get_args(args)
            assert isinstance(x, Integer) and isinstance(y, Integer)
            return Integer(int(x.value) ^ int(y.value))
        elif opcode == LLVMShl:
            x, y = self._get_args(args)
            assert isinstance(x, Integer) and isinstance(y, Integer)
            return Integer(int(x.value) << int(y.value))

        elif opcode == LLVMCall:
            if self.has_function(args[-1]):
                for index in range(LLVMCountParams(args[-1])):
                    param = LLVMGetParam(args[-1], index)
                    self.global_state.set_variable(rffi.cast(rffi.INT, param),\
                                                   self.lookup_var(args[index]))
                interp_fun = Interpreter(self.functions, self.global_state)
                return interp_fun.run(args[-1])
            else:
                string_format_ref = LLVMGetOperand(args[0], 0)
                str_var = self.lookup_var(string_format_ref)
                assert isinstance(str_var, String)
                string_format = str_var.value
                fn_name = rffi.charp2str(LLVMGetValueName(args[-1]))
                if fn_name == "printf" or fn_name == "puts":
                    printf_args = []
                    for i in range(1, len(args) - 1):
                        arg = args[i]
                        var = self.lookup_var(arg)
                        printf_args.append(var)
                    self.puts(string_format, printf_args)
                else:
                    self.exit_not_implemented(fn_name)
        elif opcode == LLVMAlloca:
            return Ptr(lltype.scoped_alloc(rffi.VOIDP.TO, 1))
        elif opcode == LLVMStore:
            # store arg[0] in arg[1]
            var = self.lookup_var(args[0])
            self.set_var(args[1], var)
        elif opcode == LLVMLoad:
            return self.lookup_var(args[0])
        elif opcode == LLVMFPExt:
            # extend a floating point value (eg float -> double)
            var_val = self.lookup_var(args[0])
            assert isinstance(var_val, Float)
            return Float(var_val.value)
        elif opcode == LLVMZExt:
            var_val = self.lookup_var(args[0])
            assert isinstance(var_val, Integer)
            return Integer(var_val.value)
        elif opcode == LLVMFPTrunc:
            # truncate a floating point value (double -> float)
            var_val = self.lookup_var(args[0])
            assert isinstance(var_val, Float)
            return Float(var_val.value)
        elif opcode == LLVMSIToFP:
            # convert Signed to Floating Point
            var_val = self.lookup_var(args[0])
            assert isinstance(var_val, Integer)
            return Float(float(var_val.value))
        elif opcode == LLVMBr:
            # if the jump is conditional, it's necessary to find
            # the block to jump to
            if LLVMIsConditional(instruction):
                cond = self.lookup_var(LLVMGetCondition(instruction))
                assert isinstance(cond, Integer)
                if cond.value == True:
                    return BasicBlock(LLVMValueAsBasicBlock(args[2]))
                else:
                    return BasicBlock(LLVMValueAsBasicBlock(args[1]))
            else:
                # unconditional jump
                return BasicBlock(LLVMValueAsBasicBlock(args[0]))
        elif opcode == LLVMICmp:
            val1 = self.lookup_var(args[0])
            val2 = self.lookup_var(args[1])
            predicate = LLVMGetICmpPredicate(instruction)
            return self.eval_condition(predicate, val1, val2)
        elif opcode == LLVMPHI:
            return self.get_phi_result(instruction)
        elif opcode == LLVMSelect:
            cond = self.lookup_var(args[0])
            assert isinstance(cond, Integer)
            if cond.value != 0:
                return self.lookup_var(args[1])
            else:
                return self.lookup_var(args[2])
        elif opcode == LLVMSwitch:
            return self.get_switch_block(args)
        else:
            self.exit_not_implemented("Unknown opcode %d" % opcode)
        return NoValue()

    def run(self, function):
        self.frame = State()
        block = LLVMGetFirstBasicBlock(function)
        while block:
            instruction = LLVMGetFirstInstruction(block)
            next_block = LLVMGetNextBasicBlock(block)
            while instruction:
                value = self.exec_operation(instruction)
                # a jump instruction has been processed
                # (it returns a basic block)
                if isinstance(value, BasicBlock):
                    next_block = value.value
                    break
                elif not isinstance(value, NoValue):
                    self.frame.set_variable(rffi.cast(rffi.INT, instruction), value)
                instruction = LLVMGetNextInstruction(instruction)
                # last instruction should be ret
                if not instruction:
                    return value
            self.last_block = block
            block = next_block

def load_func_table(module):
    ''' Creates the function table for the interpreter. '''

    functions = {}
    function = LLVMGetFirstFunction(module)
    while function:
        if not LLVMIsDeclaration(function):
            functions[rffi.cast(rffi.INT, function)] = function
        function = LLVMGetNextFunction(function)
    return functions

def load_globals(module, global_state, main_argc, main_argv):
    ''' Loads the global variables for the interpreter, including
        the argc and argv. '''

    global_var = LLVMGetFirstGlobal(module)
    main_fun = LLVMGetNamedFunction(module, "main")
    while global_var:
        with lltype.scoped_alloc(rffi.INTP.TO, 1) as int_ptr:
            initializer = LLVMGetInitializer(global_var)
            if LLVMIsConstantString(initializer):
                string_var = LLVMGetAsString(initializer, int_ptr)
                global_state.set_variable(rffi.cast(rffi.INT, global_var),\
                                          String(rffi.charp2str(string_var)))
            else:
                print "[ERROR]: Found a non-string global variable."
                raise TypeError(rffi.charp2str(LLVMPrintValueToString(initializer)))
        global_var = LLVMGetNextGlobal(global_var)
    # setting argc and argv of the C program - currently global vars
    for index in range(LLVMCountParams(main_fun)):
        param = LLVMGetParam(main_fun, index)
        if index == 0:
            global_state.set_variable(rffi.cast(rffi.INT, param),\
                                                Integer(main_argc))
        else:
            global_state.set_variable(rffi.cast(rffi.INT, param),\
                                                List(main_argv))

def create_module(filename):
    ''' Returns the module created with the contents of the given file. '''

    module = LLVMModuleCreateWithName("module")
    with lltype.scoped_alloc(rffi.CCHARPP.TO, 1) as out_message:
        with lltype.scoped_alloc(rffi.VOIDP.TO, 1) as mem_buff:
            with lltype.scoped_alloc(rffi.VOIDPP.TO, 1) as mem_buff_ptr:
                mem_buff_ptr[0] = mem_buff
                rc = LLVMCreateMemoryBufferWithContentsOfFile(filename, mem_buff_ptr, out_message)
                if rc != 0:
                    print"[ERROR]: Cannot create memory buffer with contents of"\
                         " %s: %s.\n" % (filename, rffi.charp2str(out_message[0]))
                    raise InvalidFileException(filename)
                mem_buff = mem_buff_ptr[0]

            with lltype.scoped_alloc(rffi.VOIDPP.TO, 1) as module_ptr:
                module_ptr[0] = module
                rc = LLVMParseBitcode(mem_buff, module_ptr, out_message)
                if rc != 0:
                    print "[ERROR]: Cannot parse %s: %s.\n" % (filename, rffi.charp2str(out_message[0]))
                    raise UnparsableBitcodeException(filename)
                module = module_ptr[0]
    return module

def main(args):
    if len(args) < 2:
        print"[ERROR]: Need an argument:\nUsage: ./llvmtest name.bc [C args]\n"
        return 1
    module = create_module(args[1])
    main_argc = len(args) - 1
    main_argv = args[1:]
    global_state = State()
    load_globals(module, global_state, main_argc, main_argv)
    interp = Interpreter(load_func_table(module), global_state)
    main_fun = LLVMGetNamedFunction(module, "main")
    interp.run(main_fun)
    return 0

if __name__ == '__main__':
   main(sys.argv)
