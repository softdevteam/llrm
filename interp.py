from __future__ import with_statement

import sys

from llvm_wrapper import *

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

        print "Mem buff is", mem_buff, rc
        with lltype.scoped_alloc(rffi.VOIDPP.TO, 1) as module_ptr:
            module_ptr[0] = module
            rc = LLVMParseBitcode(mem_buff, module_ptr, out_message)
            if rc != 0:
                print "[ERROR]: Cannot parse %s: %s.\n" % (args[1], rffi.charp2str(out_message[0]))
                return 3
            module = module_ptr[0]
        main_fun = LLVMGetNamedFunction(module, "main")

    print "The whole module:\n%s" % rffi.charp2str(LLVMPrintModuleToString(module))
    
    with lltype.scoped_alloc(rffi.VOIDPP.TO, 1) as basic_blocks_main_ptr:
        LLVMGetBasicBlocks(main_fun, basic_blocks_main_ptr)
        basic_blocks_main = basic_blocks_main_ptr[0]

    print "\n%s has: \n" % rffi.charp2str(LLVMGetValueName(main_fun))

    block = LLVMGetFirstBasicBlock(main_fun)

    while lltype.normalizeptr(block) is not None:
        instruction = LLVMGetFirstInstruction(block)
        while lltype.normalizeptr(instruction) is not None:
            operands = LLVMGetNumOperands(instruction)
            opcode = LLVMGetInstructionOpcode(instruction)
            print "\t%d has operands:\n" % opcode
            for i in range(0, operands):
                operand = LLVMGetOperand(instruction, i)
                print "\t\toperand %d: %s\n" % (i,
                        rffi.charp2str(LLVMPrintValueToString(operand)))
            print "\n"
            instruction = LLVMGetNextInstruction(instruction)
        block = LLVMGetNextBasicBlock(block)
    return 0

if __name__ == '__main__':
   main(sys.argv)
