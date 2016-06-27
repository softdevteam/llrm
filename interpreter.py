from __future__ import with_statement
from rpython.rlib import jit
from type_wrapper import String, Integer, Float, Ptr, List, Value, NoValue, NumericValue
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
        if rffi.cast(rffi.INT, function) in self.functions:
            return True
        return False

    def exec_operation(self, instruction):
        opcode = LLVMGetInstructionOpcode(instruction)
        args = [LLVMGetOperand(instruction, i)\
                for i in range(LLVMGetNumOperands(instruction))]
        if opcode == LLVMRet:
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
        elif opcode == LLVMSub:
            x, y = self._get_args(args)
            assert isinstance(x, Integer) and isinstance(y, Integer)
            return Integer(x.value - y.value)
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
        else:
            self.exit_not_implemented("Unknown opcode")
        return NoValue()

    def run(self, function):
        self.frame = State()
        block = LLVMGetFirstBasicBlock(function)
        while block:
            instruction = LLVMGetFirstInstruction(block)
            while instruction:
                value = self.exec_operation(instruction)
                if not isinstance(value, NoValue):
                    self.frame.set_variable(rffi.cast(rffi.INT, instruction), value)
                instruction = LLVMGetNextInstruction(instruction)
                # last instruction should be ret
                if not instruction:
                    return value
            block = LLVMGetNextBasicBlock(block)

def load_func_table(module):
    functions = {}
    function = LLVMGetFirstFunction(module)
    while function:
        if not LLVMIsDeclaration(function):
            functions[rffi.cast(rffi.INT, function)] = function
        function = LLVMGetNextFunction(function)
    return functions

def load_globals(module, global_state, main_argc, main_argv):
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

def main(args):
    if len(args) < 2:
        print"[ERROR]: Need an argument:\nUsage: ./llvmtest name.bc [C args]\n"
        return 1

    module = LLVMModuleCreateWithName("module_test")

    with lltype.scoped_alloc(rffi.CCHARPP.TO, 1) as out_message:
        #mem_buff = lltype.malloc(rffi.VOIDP.TO, 1, flavor="raw")
        with lltype.scoped_alloc(rffi.VOIDP.TO, 1) as mem_buff:
            with lltype.scoped_alloc(rffi.VOIDPP.TO, 1) as mem_buff_ptr:
                mem_buff_ptr[0] = mem_buff
                rc = LLVMCreateMemoryBufferWithContentsOfFile(args[1], mem_buff_ptr, out_message)
                if rc != 0:
                    print"[ERROR]: Cannot create memory buffer with contents of"\
                         " %s: %s.\n" % (args[1], rffi.charp2str(out_message[0]))
                    return 2
                mem_buff = mem_buff_ptr[0]

            with lltype.scoped_alloc(rffi.VOIDPP.TO, 1) as module_ptr:
                module_ptr[0] = module
                rc = LLVMParseBitcode(mem_buff, module_ptr, out_message)
                if rc != 0:
                    print "[ERROR]: Cannot parse %s: %s.\n" % (args[1], rffi.charp2str(out_message[0]))
                    return 3
                module = module_ptr[0]

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
