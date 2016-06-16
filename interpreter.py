from __future__ import with_statement

import sys

from rpython.rlib import jit
from llvm_wrapper import *

def target(*args):
    return main, None

def jitpolicy(driver):
    from rpython.jit.codewriter.policy import JitPolicy
    return JitPolicy()

jit_driver = jit.JitDriver (
    greens = [],
    reds = []
)

def LLVMShl_op(operand_list = []):
    print "shift left", operand_list

def LLVMOr_op(operand_list = []):
    print "or", operand_list

def LLVMAdd_op(operand_list = []):
    print "add", operand_list

def LLVMMul_op(operand_list = []):
    print "mult", operand_list

def LLVMRet_op(operand_list = []):
    print "return", operand_list

def LLVMCall_op(operand_list = []):
    print "Call", operand_list

def LLVMAlloca_op(operand_list = []):
    print "Alloca", operand_list

def LLVMStore_op(operand_list = []):
    print "store", operand_list

def LLVMLoad_op(operand_list = []):
    print "loading", operand_list

class UnknownOpcodeException(Exception):
    pass

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

    block = LLVMGetFirstBasicBlock(main_fun)

    while block:
        instruction = LLVMGetFirstInstruction(block)
        while instruction:
            operands = LLVMGetNumOperands(instruction)
            opcode = LLVMGetInstructionOpcode(instruction)

            #if opcode not in range(1, 66):
            #    raise UnknownOpcodeException(opcode)

            operand_list = []
            for i in range(0, operands):
                operand = LLVMPrintValueToString(LLVMGetOperand(instruction, i))
                operand_list.append(rffi.charp2str(operand))

            if opcode == LLVMRet:
                LLVMRet_op(operand_list)
            elif opcode == LLVMAdd:
                LLVMAdd_op(operand_list)
            elif opcode == LLVMMul:
                LLVMMul_op(operand_list)
            elif opcode == LLVMCall:
                LLVMCall_op(operand_list)
            elif opcode == LLVMAlloca:
                LLVMAlloca_op(operand_list)
            elif opcode == LLVMStore:
                LLVMStore_op(operand_list)
            elif opcode == LLVMOr:
                LLVMOr_op(operand_list)
            elif opcode == LLVMLoad:
                LLVMLoad_op(operand_list)
            else:
                raise UnknownOpcodeException(opcode)
            instruction = LLVMGetNextInstruction(instruction)
            print "\n"

        block = LLVMGetNextBasicBlock(block)
    return 0

if __name__ == '__main__':
   main(sys.argv)
