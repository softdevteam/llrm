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

# XXX not yet implemented
class Interpreter(object):
    def __init__(self):
        stack = []
        global_state = State()

def main(args):
    if len(args) < 2:
        print"[ERROR]: Need an argument:\nUsage: ./llvmtest name.bc\n"
        return 1

    # argc and argv of the C program
    c_argc = 0
    c_argv = []
    if len(args) > 2:
        c_argc = int(args[2])
        if c_argc > 0:
            c_argv = args[3:]

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

    interp = Interpreter()
    # stack frame for main
    frame = State()

    block = LLVMGetFirstBasicBlock(main_fun)
    while block:
        instruction = LLVMGetFirstInstruction(block)
        while instruction:
            opcode = LLVMGetInstructionOpcode(instruction)

            operand_list = [LLVMGetOperand(instruction, i) \
                            for i in range(0,  LLVMGetNumOperands(instruction))]

            operation = Operation(opcode, operand_list)
            value = operation.execute(frame)
            frame.set_variable(rffi.cast(rffi.INT, instruction), value)

            instruction = LLVMGetNextInstruction(instruction)

        block = LLVMGetNextBasicBlock(block)
    print frame.vars, frame.var_offsets.items()
    return 0

if __name__ == '__main__':
   main(sys.argv)
