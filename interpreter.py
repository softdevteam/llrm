from __future__ import with_statement

import sys

from rpython.rlib import jit
from llvm_wrapper import *
from state import State
from type_wrapper import *

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

def lookup_var(local_vars, global_vars, var):
    ''' Returns the value of a variable. First checks locals, then globals'''

    if local_vars.has_key(rffi.cast(rffi.INT, var)):
        return local_vars.get_variable(rffi.cast(rffi.INT, var))
    elif global_vars.has_key(rffi.cast(rffi.INT, var)):
        return global_vars.get_variable(rffi.cast(rffi.INT, var))
    elif LLVMIsConstant(var):
        var_type = LLVMGetTypeKind(LLVMTypeOf(var))
        if var_type == LLVMIntegerTypeKind:
            return Integer(LLVMConstIntGetSExtValue(var))
        elif var_type == LLVMDoubleTypeKind:
            with lltype.scoped_alloc(rffi.SIGNEDP.TO, 1) as signed_ptr:
                return Float(LLVMConstRealGetDouble(var, signed_ptr))
        else:
            print "[ERROR]: Unknown type. Exiting."
            raise NoSuchTypeException(rffi.charp2str(LLVMPrintTypeToString(LLVMTypeOf(var))))
    else:
        print "[ERROR]: Unknown variable. Exiting."
        raise NoSuchVariableException(rffi.charp2str(LLVMPrintValueToString(var)))
    return Type()

class Interpreter(object):

    def __init__(self, functions, global_state = None):
        self.functions = functions
        self.global_state = global_state

    # only works for integers
    def _get_args(self, args, state):
        ''' Returns a list of arguments represented as integers '''

        arg_vals = []
        for arg in args:
            arg_vals.append(lookup_var(state, self.global_state, arg))
        return arg_vals

    def exit_not_implemented(self, name):
        print "[ERROR]: Found unimplemented operation. Exiting."
        raise NotImplementedError(name)

    def exec_operation(self, state, opcode, args=[]):
        if opcode == LLVMRet:
            return Integer(0)
        elif opcode == LLVMAdd:
            x, y = self._get_args(args, state)
            assert isinstance(x, NumericType) and isinstance(y, NumericType)
            return Integer(x.value + y.value)
        elif opcode == LLVMMul:
            x, y = self._get_args(args, state)
            assert isinstance(x, NumericType) and isinstance(y, NumericType)
            return Integer(x.value * y.value)
        elif opcode == LLVMSub:
            x, y = self._get_args(args, state)
            assert isinstance(x, NumericType) and isinstance(y, NumericType)
            return Integer(x.value - y.value)
        elif opcode == LLVMCall:
            # TODO implement function calls

            if rffi.cast(rffi.INT, args[-1]) in self.functions.keys():
                print "found function", rffi.charp2str(LLVMGetValueName(args[-1]))
            else:
                print rffi.charp2str(LLVMGetValueName(args[-1]))
                string_format_ref = LLVMGetOperand(args[0], 0)
                str_var = lookup_var(state, self.global_state, string_format_ref)
                assert isinstance(str_var, String)
                string_format = str_var.value
                fn_name = rffi.charp2str(LLVMGetValueName(args[-1]))
                if fn_name == "printf":
                    printf_args = []
                    for i in range(1, len(args) - 1):
                        arg = args[i]
                        var = lookup_var(state, self.global_state, arg)
                        printf_args.append(var)
                    print string_format
                    if len(printf_args) > 0:
                        print "Arguments are: "
                        for arg in printf_args:
                            assert isinstance(arg, NumericType)
                            print arg.value
                        print "\n\n"
                elif fn_name == "puts":
                    print string_format
                else:
                    self.exit_not_implemented(fn_name)
        elif opcode == LLVMAlloca:
            self.exit_not_implemented("LLVMStore")
        elif opcode == LLVMStore:
            # store arg[0] in arg[1]
            self.exit_not_implemented("LLVMStore")
        return Integer(0)

    def run(self, function):
        frame = State()
        block = LLVMGetFirstBasicBlock(function)
        while block:
            instruction = LLVMGetFirstInstruction(block)
            while instruction:
                opcode = LLVMGetInstructionOpcode(instruction)

                operand_list = [LLVMGetOperand(instruction, i)\
                                for i in range(0,  LLVMGetNumOperands(instruction))]

                value = self.exec_operation(frame, opcode, operand_list)
                frame.set_variable(rffi.cast(rffi.INT, instruction), value)
                instruction = LLVMGetNextInstruction(instruction)
            block = LLVMGetNextBasicBlock(block)

def main(args):
    if len(args) < 2:
        print"[ERROR]: Need an argument:\nUsage: ./llvmtest name.bc [C args]\n"
        return 1

    module = LLVMModuleCreateWithName("module_test")

    with lltype.scoped_alloc(rffi.CCHARPP.TO, 1) as out_message:
        mem_buff = lltype.malloc(rffi.VOIDP.TO, 1, flavor="raw")
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
        main_fun = LLVMGetNamedFunction(module, "main")

    with lltype.scoped_alloc(rffi.VOIDPP.TO, 1) as basic_blocks_main_ptr:
        LLVMGetBasicBlocks(main_fun, basic_blocks_main_ptr)
        basic_blocks_main = basic_blocks_main_ptr[0]

    global_state = State()
    global_var = LLVMGetFirstGlobal(module)

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

    main_argc = len(args) - 2
    main_argv = args[2:]

    # setting argc and argv of the C program
    # warning: argc and argv are currently accessible
    # anywhere in the program - they are global vars
    for index in range(0, LLVMCountParams(main_fun)):
        param = LLVMGetParam(main_fun, index)
        if index == 0:
            global_state.set_variable(rffi.cast(rffi.INT, param),\
                                                Integer(main_argc))
        else:
            global_state.set_variable(rffi.cast(rffi.INT, param),\
                                                List(main_argv))
    functions = {}
    function = LLVMGetFirstFunction(module)
    while function:
        if not LLVMIsDeclaration(function):
            functions[rffi.cast(rffi.INT, function)] = function
        function = LLVMGetNextFunction(function)
    interp = Interpreter(functions, global_state)
    interp.run(main_fun)
    return 0

if __name__ == '__main__':
   main(sys.argv)
