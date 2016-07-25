from rpython.rlib import jit
from state import State
from type_wrapper import Integer, Float, List, String
from rpython.rtyper.lltypesystem import rffi, lltype

import llvm_wrapper as llwrap

class W_Module(object):
    ''' Represents a wrapper for an LLVMModuleRef. '''

    _immutable_fields_ = ['w_main_fun', 'l_module']

    def __init__(self, l_module):
        self.l_module = l_module
        self.function_offsets = {}
        self.w_functions = []
        self._initialize_functions()
        self.w_main_fun = W_Function(llwrap.LLVMGetNamedFunction(l_module, "main"), self)

    def _initialize_functions(self):
        l_func = llwrap.LLVMGetFirstFunction(self.l_module)
        while l_func:
            # only storing functions defined internally
            if not llwrap.LLVMIsDeclaration(l_func):
                self._set_function(l_func, W_Function(l_func, self))
            l_func = llwrap.LLVMGetNextFunction(l_func)

    def _set_function(self, l_function, w_function):
        addr = rffi.cast(rffi.INT, l_function)
        offset = self._get_func_off(addr)
        self.w_functions[offset] = w_function

    def get_function(self, l_func):
        ''' Returns the W_Function representation of a given function of
            this module.'''

        if self.has_function(l_func):
            addr = rffi.cast(rffi.INT, l_func)
            offset = self._get_func_off(addr)
            return self.w_functions[offset]
        else:
            raise LookupError(rffi.charp2str(llwrap.LLVMPrintValueToString(l_func)))

    @jit.elidable_promote()
    def _get_func_off(self, l_func):
        offset = self.function_offsets.get(l_func, -1)
        if offset == -1:
            offset = len(self.w_functions)
            self.function_offsets[rffi.cast(rffi.INT, l_func)] = offset
            self.w_functions.append(None)
        return offset

    def has_function(self, l_function):
        ''' Checks if this W_Module contains a given function. '''

        addr = rffi.cast(rffi.INT, l_function)
        offset = self.function_offsets.get(addr, -1)
        return offset != -1

    def load_globals(self, global_state, main_argc, main_argv):
        ''' Loads the global variables into a given State object and sets
            argc and argv. '''

        l_global_var = llwrap.LLVMGetFirstGlobal(self.l_module)
        l_main_fun = llwrap.LLVMGetNamedFunction(self.l_module, "main")
        while l_global_var:
            l_initializer = llwrap.LLVMGetInitializer(l_global_var)
            addr = rffi.cast(rffi.INT, l_global_var)
            if llwrap.LLVMIsConstantString(l_initializer):
                with lltype.scoped_alloc(rffi.INTP.TO, 1) as int_ptr:
                    l_string_var = llwrap.LLVMGetAsString(l_initializer, int_ptr)
                    global_state.set_variable(rffi.cast(rffi.INT, l_global_var),\
                                              String(rffi.charp2str(l_string_var)))
            else:
                print "[ERROR]: Unknown type. Exiting."
                raise TypeError(rffi.charp2str(llwrap.LLVMPrintValueToString(l_initializer)))
            l_global_var = llwrap.LLVMGetNextGlobal(l_global_var)
        # setting argc and argv of the C program - currently global vars
        for index in range(llwrap.LLVMCountParams(l_main_fun)):
            l_param = llwrap.LLVMGetParam(l_main_fun, index)
            if index == 0:
                global_state.set_variable(rffi.cast(rffi.INT, l_param),\
                                                    Integer(main_argc))
            else:
                global_state.set_variable(rffi.cast(rffi.INT, l_param),\
                                                    List(main_argv))

class W_Function(object):
    ''' Represents a wrapper for an LLVMValueRef that is a function. '''

    _immutable_fields_ = ['name']

    def __init__(self, l_function, w_module):
        self.block_offsets = {}
        self.w_blocks = []
        self._initialize_blocks(l_function, w_module)
        self.name = rffi.charp2str(llwrap.LLVMGetValueName(l_function))
        self._set_instr_blocks()

    def _initialize_blocks(self, l_function, w_module):
        l_block = llwrap.LLVMGetFirstBasicBlock(l_function)
        prev = None
        while l_block:
            current_block = W_Block(l_block, w_module)
            if prev:
                prev.w_next_block = current_block
            prev = current_block
            self._set_block(l_block, current_block)
            l_block = llwrap.LLVMGetNextBasicBlock(l_block)

    def _set_block(self, l_block, w_block):
        addr = rffi.cast(rffi.INT, l_block)
        offset = self._get_block_off(addr)
        self.w_blocks[offset] = w_block

    def _set_instr_blocks(self):
        block = self.get_first_block()
        while block:
            instruction = block.get_first_instruction()
            while instruction:
                if isinstance(instruction, W_PhiInstruction):
                    incoming_block = []
                    for i in range(instruction.count_incoming):
                        l_block = llwrap.LLVMGetIncomingBlock(instruction.l_instr, i)
                        w_block = self.get_block(l_block)
                        incoming_block.append(w_block)
                    instruction.incoming_block = incoming_block[:]
                elif isinstance(instruction, W_BrInstruction):
                    l_block = llwrap.LLVMValueAsBasicBlock(instruction.operands[0].l_value)
                    instruction.w_bb_uncond = self.get_block(l_block)
                elif isinstance(instruction, W_ConditionalInstruction):
                    l_block_true = llwrap.LLVMValueAsBasicBlock(instruction.operands[2].l_value)
                    l_block_false = llwrap.LLVMValueAsBasicBlock(instruction.operands[1].l_value)
                    instruction.w_bb_true = self.get_block(l_block_true)
                    instruction.w_bb_false = self.get_block(l_block_false)
                elif isinstance(instruction, W_SwitchInstruction):
                    instruction.default_branch = self.get_block(instruction.operands[1].l_value)
                    w_blocks = []
                    for i in range(3, len(instruction.operands), 2):
                        w_blocks.append(self.get_block(instruction.operands[i].l_value))
                    instruction.w_blocks = w_blocks[:]
                instruction = instruction.w_next_instr
            block = block.w_next_block

    @jit.elidable_promote()
    def get_block(self, l_block):
        ''' Returns the W_Block representation of a given block of
            this function.'''

        if self.has_block(l_block):
            addr = rffi.cast(rffi.INT, l_block)
            offset = self._get_block_off(addr)
            return self.w_blocks[offset]
        else:
            raise LookupError(self._get_block_string(l_block))

    @jit.elidable_promote()
    def _get_block_string(self, l_block):
        return rffi.charp2str(llwrap.LLVMPrintValueToString(l_block))

    @jit.elidable_promote()
    def _get_block_off(self, l_block):
        offset = self.block_offsets.get(l_block, -1)
        if offset == -1:
            offset = len(self.w_blocks)
            self.block_offsets[rffi.cast(rffi.INT, l_block)] = offset
            self.w_blocks.append(None)
        return offset

    def has_block(self, l_block):
        ''' Checks if this W_Function contains a given block. '''

        addr = rffi.cast(rffi.INT, l_block)
        offset = self.block_offsets.get(addr, -1)
        if offset == -1:
            return False
        return True

    def get_first_block(self):
        ''' Returns the first block in this function. '''

        return self.w_blocks[0]

class W_Block(object):
    ''' Represents a wrapper for an LLVMBasicBlockRef. '''

    _immutable_fields_ = ['w_next_block', 'l_value', 'w_instructions[*]']

    def __init__(self, l_block, w_module):
        self.w_instructions = self._get_instructions(l_block, w_module)[:]
        self.w_next_block = None
        self.l_value = llwrap.LLVMValueAsBasicBlock(l_block)

    def _get_instructions(self, l_block, w_module):
        l_instr = llwrap.LLVMGetFirstInstruction(l_block)
        w_instrs = []
        prev = None
        while l_instr:
            current_instr = _get_instruction(llwrap.LLVMGetInstructionOpcode(l_instr),
                                             l_instr, w_module)
            if prev:
                prev.w_next_instr = current_instr
            prev = current_instr
            w_instrs.append(current_instr)
            l_instr = llwrap.LLVMGetNextInstruction(l_instr)
        return w_instrs

    def get_first_instruction(self):
        ''' Returns the first instruction in this basic block. '''

        return self.w_instructions[0]

    def __eq__(self, other):
        if isinstance(other, W_Block):
            return self.w_instructions == other.w_instructions and\
                   self.l_value == other.l_value
        return NotImplemented

class W_BaseInstruction(object):
    ''' Represents a wrapper for an LLVMValueRef that is an instruction. '''

    _immutable_fields_ = ['addr', 'operands[*]', 'opcode', 'w_next_instr',\
                          'name']

    def __init__(self, l_instr, w_module):
        self.addr = rffi.cast(rffi.INT, l_instr)
        self.operands = self._get_operands(l_instr, w_module)
        self.opcode = llwrap.LLVMGetInstructionOpcode(l_instr)
        self.w_next_instr = None
        self.name = rffi.charp2str(llwrap.LLVMPrintValueToString(l_instr))

    def is_conditional(self):
        ''' Checks if this instruction is a conditional instruction. '''

        return isinstance(self, W_ConditionalInstruction)

    def _get_operands(self, l_instr, w_module):
        ''' Returns the operands of this instruction and stores the
            constant ones in the given W_Module. '''

        args = []
        for i in range(llwrap.LLVMGetNumOperands(l_instr)):
            arg = llwrap.LLVMGetOperand(l_instr, i)
            args.append(_get_variable_wrapper(arg))
        return args

class W_BrInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a br instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)
        self.w_bb_uncond = None

class W_ConditionalInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a conditional
        br instruction. '''

    _immutable_fields_ = ['condition', 'w_bb_true', 'w_bb_false']

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)
        self.condition = _get_variable_wrapper(llwrap.LLVMGetCondition(l_instr))
        self.l_bb_true = llwrap.LLVMValueAsBasicBlock(self.operands[2].l_value)
        self.l_bb_false = llwrap.LLVMValueAsBasicBlock(self.operands[1].l_value)

class W_ICmpInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an icmp
        instruction. '''

    _immutable_fields_ = ['icmp_predicate']

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)
        self.icmp_predicate = llwrap.LLVMGetICmpPredicate(l_instr)

class W_PhiInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a phi
        instruction. '''

    _immutable_fields_ = ['l_instr', 'count_incoming', 'incoming_block[*]',
                          'incoming_value[*]']

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)
        self.l_instr = l_instr
        self.count_incoming = llwrap.LLVMCountIncoming(l_instr)
        self.incoming_block = None
        incoming_value = []
        for i in range(self.count_incoming):
            wrapped_var = _get_variable_wrapper(llwrap.LLVMGetIncomingValue(l_instr, i))
            incoming_value.append(wrapped_var)
        self.incoming_value =  incoming_value[:]

class W_CallInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a call
        instruction. '''

    _immutable_fields_ = ['func_param_count', 'string_format_ref']

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)
        if not llwrap.LLVMIsDeclaration(self.operands[-1].l_value):
            self.func_param_count = llwrap.LLVMCountParams(self.operands[-1].l_value)
            self.l_func_params = []
            for index in range(self.func_param_count):
                wrapped_var = _get_variable_wrapper(llwrap.LLVMGetParam(self.operands[-1].l_value, index))
                self.l_func_params.append(wrapped_var)
        else:
            # assume the instruction is either printf or puts (this is checked by the
            # the interpreter)
            self.string_format_ref = _get_variable_wrapper(llwrap.LLVMGetOperand(self.operands[0].l_value, 0))
            self.func_name = rffi.charp2str(llwrap.LLVMGetValueName(self.operands[-1].l_value))

class W_SwitchInstruction(W_BaseInstruction):

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)
        self.default_branch = None
        self.w_blocks = None

def _get_instruction(opcode, l_instruction, w_module):
    ''' Returns the appropriate wrapper for the specified instruction. '''

    if opcode == llwrap.LLVMBr:
        if llwrap.LLVMIsConditional(l_instruction):
            return W_ConditionalInstruction(l_instruction, w_module)
        else:
            return W_BrInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMICmp:
        return W_ICmpInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMPHI:
        return W_PhiInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMCall:
        return W_CallInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMSwitch:
        return W_SwitchInstruction(l_instruction, w_module)
    else:
        return W_BaseInstruction(l_instruction, w_module)

class Variable(object):

    def __init__(self, l_value):
        self.addr = rffi.cast(rffi.INT, l_value)
        self.l_value = l_value

class LocalVariable(Variable):

    def __init__(self, content, l_value):
        Variable.__init__(self, l_value)
        self.content = content

class GlobalVariable(Variable):

    def __init__(self, content, l_value):
        Variable.__init__(self, l_value)
        self.content = content

class Constant(Variable):

    def __init__(self, content, l_value):
        Variable.__init__(self, l_value)
        self.content = content

def _get_variable_wrapper(l_val):
    ''' Returns the correct variable wrapper for a given LLVMValueRef. '''

    value = Variable(l_val)
    if llwrap.LLVMIsConstant(l_val):
        val_type = llwrap.LLVMGetTypeKind(llwrap.LLVMTypeOf(l_val))
        if val_type == llwrap.LLVMIntegerTypeKind:
            if llwrap.LLVMIsUndef(l_val):
                value = Constant(Integer(0), l_val)
            else:
                value = Constant(Integer(llwrap.LLVMConstIntGetSExtValue(l_val)),
                                 l_val)
        elif val_type == llwrap.LLVMDoubleTypeKind or val_type == llwrap.LLVMFloatTypeKind:
            if llwrap.LLVMIsUndef(l_val):
                value = Constant(Float(0.0), l_val)
            else:
                with lltype.scoped_alloc(rffi.SIGNEDP.TO, 1) as signed_ptr:
                    fl_var = Float(llwrap.LLVMConstRealGetDouble(l_val, signed_ptr))
                    value = Constant(fl_var, l_val)
    return value
