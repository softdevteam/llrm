from __future__ import with_statement

import sys

from rpython.rlib import jit
from llvm_wrapper import *
from state import State
from operation import Operation

def target(*args):
    return main, None

def jitpolicy(driver):
    from rpython.jit.codewriter.policy import JitPolicy
    return JitPolicy()

jit_driver = jit.JitDriver (
    greens = [],
    reds = []
)

class Interpreter(object):

    not_set = True

    def __init__(self, global_state = None):
        self.stack = []
        self.pc = 0
        self.global_state = global_state

    # only works for integers
    # XXX if a value is not local (not in state) need to check
    # in global_state
    def _get_args(self, args, state):
        ''' Returns a list of arguments represented as integers '''

        arg_vals = []
        for arg in args:
            if LLVMIsConstant(arg):
                arg_vals.append(LLVMConstIntGetSExtValue(arg))
            else:
                # XXX temporary dummy value for argc is 3
                if Interpreter.not_set and "argc" in rffi.charp2str(LLVMPrintValueToString(arg)):
                    state.set_variable(rffi.cast(rffi.INT, arg), 3)
                    Interpreter.not_set = False
                arg_vals.append(state.get_variable(rffi.cast(rffi.INT, arg)))
        return arg_vals

    def exec_operation(self, state, opcode, args=[]):
        if opcode == LLVMRet:
            return 0
        elif opcode == LLVMAdd:
            x, y = self._get_args(args, state)
            return x + y
        elif opcode == LLVMMul:
            x, y = self._get_args(args, state)
            return x * y
        elif opcode == LLVMCall:
            string_format_ref = LLVMGetOperand(args[0], 0)
            string_format = None
            # need to access @.str value
            if state.has_key(rffi.cast(rffi.INT, string_format_ref)):
                string_format = state.get_variable(rffi.cast(rffi.INT, string_format_ref))
            elif self.global_state.has_key(rffi.cast(rffi.INT, string_format_ref)):
                string_format = self.global_state.get_variable(rffi.cast(rffi.INT, string_format_ref))
            else:
                print "error"
            fn_name = rffi.charp2str(LLVMGetValueName(args[-1]))
            if fn_name == "printf":
                # XXX assumes all printf arguments are integers
                printf_args = [state.get_variable(rffi.cast(rffi.INT, arg)) \
                                for arg in args[1:-1] ]
                print string_format % tuple(printf_args)
            else:
                raise NotImplementedError(fn_name)
        elif opcode == LLVMAlloca:
            pass
        elif opcode == LLVMStore:
            pass

    def run(self, main_fun):
        frame = State()

        block = LLVMGetFirstBasicBlock(main_fun)
        while block:
            instruction = LLVMGetFirstInstruction(block)
            while instruction:
                opcode = LLVMGetInstructionOpcode(instruction)

                operand_list = [LLVMGetOperand(instruction, i) \
                                for i in range(0,  LLVMGetNumOperands(instruction))]

                value = self.exec_operation(frame, opcode, operand_list)
                frame.set_variable(rffi.cast(rffi.INT, instruction), value)

                instruction = LLVMGetNextInstruction(instruction)

            block = LLVMGetNextBasicBlock(block)
        print "Done.\n[INFO]", frame.vars, frame.var_offsets.items()

def main(args):
    if len(args) < 2:
        print"[ERROR]: Need an argument:\nUsage: ./llvmtest name.bc\n"
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

    # assuming all global_vars are strings
    while global_var:
        with lltype.scoped_alloc(rffi.INTP.TO, 1) as int_ptr:
            string_var = LLVMGetAsString(LLVMGetInitializer(global_var), int_ptr)
            global_state.set_variable(rffi.cast(rffi.INT, global_var), rffi.charp2str(string_var))

        global_var = LLVMGetNextGlobal(global_var)

    interp = Interpreter(global_state)
    interp.run(main_fun)
    return 0

if __name__ == '__main__':
   main(sys.argv)
