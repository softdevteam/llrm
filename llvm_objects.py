from rpython.rlib import jit
from llvm_wrapper import *

class W_Module(object):

    def __init__(self, l_module):
        from state import State
        self.constants = State()
        self.l_module = l_module
        self.function_offsets = {}
        self.w_functions = []
        self.get_functions()
        self.w_main_fun = W_Function(LLVMGetNamedFunction(l_module, "main"), self)

    def get_functions(self):
        l_func = LLVMGetFirstFunction(self.l_module)
        while l_func:
            if not LLVMIsDeclaration(l_func):
                # we only want functiones defined internally
                self._set_function(l_func, W_Function(l_func, self))
            l_func = LLVMGetNextFunction(l_func)

    def get_function(self, l_func):
        if self.has_key(l_func):
            addr = rffi.cast(rffi.INT, l_func)
            offset = self._get_func_off(addr)
            return self.w_functions[offset]
        else:
            raise LookupError(rffi.charp2str(LLVMPrintValueToString(l_func)))

    @jit.elidable_promote()
    def _get_func_off(self, l_func):
        offset = self.function_offsets.get(l_func, -1)
        if offset == -1:
            offset = len(self.w_functions)
            self.function_offsets[rffi.cast(rffi.INT, l_func)] = offset
            self.w_functions.append(None)
        return offset

    def _set_function(self, l_function, w_function):

        addr = rffi.cast(rffi.INT, l_function)
        offset = self._get_func_off(addr)
        self.w_functions[offset] = w_function

    def has_key(self, l_function):

        addr = rffi.cast(rffi.INT, l_function)
        offset = self.function_offsets.get(addr, -1)
        if offset == -1:
            return False
        return True

    def load_globals(self, global_state, main_argc, main_argv):

        l_global_var = LLVMGetFirstGlobal(self.l_module)
        l_main_fun = LLVMGetNamedFunction(self.l_module, "main")
        while l_global_var:
            l_initializer = LLVMGetInitializer(l_global_var)
            addr = rffi.cast(rffi.INT, l_global_var)
            if LLVMIsConstantString(l_initializer):
                with lltype.scoped_alloc(rffi.INTP.TO, 1) as int_ptr:
                    l_string_var = LLVMGetAsString(l_initializer, int_ptr)
                    from type_wrapper import String
                    global_state.set_variable(rffi.cast(rffi.INT, l_global_var),\
                                              String(rffi.charp2str(l_string_var)))

            else:
                print "[ERROR]: Unknown type. Exiting."
                raise TypeError(rffi.charp2str(LLVMPrintValueToString(l_initializer)))
            l_global_var = LLVMGetNextGlobal(l_global_var)
        # setting argc and argv of the C program - currently global vars
        for index in range(LLVMCountParams(l_main_fun)):
            l_param = LLVMGetParam(l_main_fun, index)
            if index == 0:
                from type_wrapper import Integer
                global_state.set_variable(rffi.cast(rffi.INT, l_param),\
                                                    Integer(main_argc))
            else:
                from type_wrapper import List
                global_state.set_variable(rffi.cast(rffi.INT, l_param),\
                                                    List(main_argv))

class W_Function(object):

    def __init__(self, l_function, w_module):
        self.block_offsets = {}
        self.w_blocks = []
        self.get_blocks(l_function, w_module)

    def get_blocks(self, l_function, w_module):
        l_block = LLVMGetFirstBasicBlock(l_function)
        prev = None
        while l_block:
            current_block = W_Block(l_block, w_module)
            if prev:
                prev.w_next_block = current_block
            prev = current_block
            self._set_block(l_block, current_block)
            l_block = LLVMGetNextBasicBlock(l_block)

    def get_block(self, l_block):
        if self.has_key(l_block):
            addr = rffi.cast(rffi.INT, l_block)
            offset = self._get_block_off(addr)
            return self.w_blocks[offset]
        else:
            raise LookupError(rffi.charp2str(LLVMPrintValueToString(l_block)))

    @jit.elidable_promote()
    def _get_block_off(self, l_block):
        offset = self.block_offsets.get(l_block, -1)
        if offset == -1:
            offset = len(self.w_blocks)
            self.block_offsets[rffi.cast(rffi.INT, l_block)] = offset
            self.w_blocks.append(None)
        return offset

    def _set_block(self, l_block, w_block):

        addr = rffi.cast(rffi.INT, l_block)
        offset = self._get_block_off(addr)
        self.w_blocks[offset] = w_block

    def has_key(self, l_block):

        addr = rffi.cast(rffi.INT, l_block)
        offset = self.block_offsets.get(addr, -1)
        if offset == -1:
            return False
        return True

    def get_first_block(self):
        return self.w_blocks[0]

class W_Block(object):

    def __init__(self, l_block, w_module):
        self.w_instructions = self.get_instructions(l_block, w_module)
        self.w_next_block = None
        self.l_value = LLVMValueAsBasicBlock(l_block)

    def get_instructions(self, l_block, w_module):
        l_instr = LLVMGetFirstInstruction(l_block)
        w_instrs = []
        prev = None
        while l_instr:
            current_instr = W_Instruction(l_instr, w_module)
            if prev:
                prev.w_next_instr = current_instr
            prev = current_instr
            w_instrs.append(current_instr)
            l_instr = LLVMGetNextInstruction(l_instr)
        return w_instrs

    def get_first_instruction(self):
        return self.w_instructions[0]

    def __eq__(self, other):
        if isinstance(other, W_Block):
            return self.w_instructions == other.w_instructions and\
                   self.l_value == other.l_value
        return NotImplemented

class W_Instruction(object):

    def __init__(self, l_instr, w_module):
        self.l_instr = l_instr
        self.l_operands = self.get_operands(l_instr, w_module)
        self.opcode = LLVMGetInstructionOpcode(l_instr)
        self.w_next_instr = None
        if self.opcode == LLVMBr:
            self.is_conditional = LLVMIsConditional(l_instr)

            if self.is_conditional:
               self.condition = LLVMGetCondition(l_instr)
               self.l_bb_true = LLVMValueAsBasicBlock(self.l_operands[2])
               self.l_bb_false = LLVMValueAsBasicBlock(self.l_operands[1])
            else:
                self.l_bb_uncond = LLVMValueAsBasicBlock(self.l_operands[0])
        elif self.opcode == LLVMICmp:
            self.icmp_predicate = LLVMGetICmpPredicate(l_instr)
        elif self.opcode == LLVMPHI:
            self.count_incoming = LLVMCountIncoming(l_instr)
            self.incoming_block = []
            self.incoming_value = []
            for i in range(self.count_incoming):
                self.incoming_block.append(LLVMGetIncomingBlock(l_instr, i))
                self.incoming_value.append(LLVMGetIncomingValue(l_instr, i))
        elif self.opcode == LLVMCall:
            if not LLVMIsDeclaration(self.l_operands[-1]):
                self.func_param_count = LLVMCountParams(self.l_operands[-1])
                self.l_func_params = []
                for index in range(self.func_param_count):
                    self.l_func_params.append(LLVMGetParam(self.l_operands[-1], index))
            else:
                self.l_string_format_ref = LLVMGetOperand(self.l_operands[0], 0)
                self.func_name = rffi.charp2str(LLVMGetValueName(self.l_operands[-1]))

    def get_operands(self, l_instr, w_module):
        args = []
        for i in range(LLVMGetNumOperands(l_instr)):
            arg = LLVMGetOperand(l_instr, i)
            args.append(arg)
            if LLVMIsConstant(arg):
                addr = rffi.cast(rffi.INT, arg)
                var_type = LLVMGetTypeKind(LLVMTypeOf(arg))
                if var_type == LLVMIntegerTypeKind:
                    from type_wrapper import Integer
                    if LLVMIsUndef(arg):
                        # XXX undefined vars
                        w_module.constants.set_variable(addr, Integer(0))
                    else:
                        w_module.constants.set_variable(addr, Integer(LLVMConstIntGetSExtValue(arg)))
                elif var_type == LLVMDoubleTypeKind or var_type == LLVMFloatTypeKind:
                    from type_wrapper import Float
                    if LLVMIsUndef(arg):
                        w_module.constants.set_variable(addr, Float(0.0))
                    else:
                        with lltype.scoped_alloc(rffi.SIGNEDP.TO, 1) as signed_ptr:
                            fl_var = Float(LLVMConstRealGetDouble(arg, signed_ptr))
                            w_module.constants.set_variable(addr, fl_var)
        return args
