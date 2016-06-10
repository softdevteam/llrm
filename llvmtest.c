#include <stdio.h>
#include <stdlib.h>
#include <llvm-c/Core.h>
#include <llvm-c/BitReader.h>

int main(int argc, char* argv[])
{
	if(argc < 2) {
		printf("[ERROR]: Need an arugment:\nUsage: ./llvmtest name.bc\n");
		return 1;
	}

	LLVMModuleRef module = LLVMModuleCreateWithName("test_module");
	LLVMMemoryBufferRef mem_buff;
	char* error = NULL;

	// reads content of .bc file
	LLVMBool error_mem_buff = LLVMCreateMemoryBufferWithContentsOfFile(argv[1],
		 						&mem_buff, &error);

	if(error_mem_buff) {
		printf("[ERROR]: Cannot create memory buffer with contents of %s: %s.\n",
		 		argv[1], error);
		LLVMDisposeModule(module);
		return 1;
	}

	int return_code = LLVMParseBitcode(mem_buff, &module, &error);

	if(return_code) {
		printf("[ERROR]: Cannot parse %s: %s.\n", argv[1], error);
		LLVMDisposeModule(module);
		return 1;
	}

	// gets a reference to the main function
	LLVMValueRef main_fun = LLVMGetNamedFunction(module, "main");

	// getting the basic blocks of the main function
	LLVMBasicBlockRef basic_blocks_main;
	LLVMGetBasicBlocks(main_fun, &basic_blocks_main);

	printf("\n%s has: \n", LLVMGetValueName(main_fun));

	// iterating through all basic blocks of main and retrieving all instruction
	// opcodes
	LLVMBasicBlockRef block;
	for(block = LLVMGetFirstBasicBlock(main_fun); block != NULL;
		block = LLVMGetNextBasicBlock(block)) {

		LLVMValueRef instruction;
		for(instruction = LLVMGetFirstInstruction(block); instruction != NULL;
			instruction = LLVMGetNextInstruction(instruction)) {

			int operands = LLVMGetNumOperands(instruction);
			LLVMOpcode opcode = LLVMGetInstructionOpcode(instruction);

    		printf("%d has operands:\n", opcode);
			for(int i = 0; i < operands; ++i) {

				LLVMValueRef operand = LLVMGetOperand(instruction, i);
				printf("operand %d: %s\n", i, LLVMPrintValueToString(operand));
			}
			printf("\n");
		}
	}

	// IR representation of the entire module
	printf("The whole module: \n\n%s\n", LLVMPrintModuleToString(module));

	printf("Functions:\n\n");

	LLVMValueRef function = LLVMGetFirstFunction(module);
	do {
		printf("%s at %p\n", LLVMGetValueName(function), (void *) function);
	} while( (function = LLVMGetNextFunction(function)) );

	LLVMDisposeModule(module);
	return 0;
}
