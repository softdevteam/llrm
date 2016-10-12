from rpython.rlib import jit
from rpython.rtyper.lltypesystem import rffi, lltype
from type_wrapper import String, Integer, Float, Ptr, Value, List, NoValue,\
                         BasicBlock

import llvm_wrapper as llwrap
import interpreter

class MissingPredecessorBasicBlockException(Exception):
    pass

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

    def load_globals(self, global_frame):
        ''' Loads the global variables into a given Frame object and sets
            argc and argv. '''

        l_global_var = llwrap.LLVMGetFirstGlobal(self.l_module)
        while l_global_var:
            l_initializer = llwrap.LLVMGetInitializer(l_global_var)
            addr = rffi.cast(rffi.INT, l_global_var)
            if llwrap.LLVMIsConstantString(l_initializer):
                with lltype.scoped_alloc(rffi.INTP.TO, 1) as int_ptr:
                    l_string_var = llwrap.LLVMGetAsString(l_initializer, int_ptr)
                    global_frame.set_variable(rffi.cast(rffi.INT, l_global_var),\
                                              String(rffi.charp2str(l_string_var)))
            else:
                print "[ERROR]: Unknown type. Exiting."
                raise TypeError(rffi.charp2str(llwrap.LLVMPrintValueToString(l_initializer)))
            l_global_var = llwrap.LLVMGetNextGlobal(l_global_var)

    def load_main(self, argc, argv):
        from state import InterpreterState
        main_frame = InterpreterState.main_frame
        l_main_fun = llwrap.LLVMGetNamedFunction(self.l_module, "main")
        for index in range(llwrap.LLVMCountParams(l_main_fun)):
            l_param = llwrap.LLVMGetParam(l_main_fun, index)
            if index == 0:
                main_frame.set_variable(rffi.cast(rffi.INT, l_param), Integer(argc))
            else:
                main_frame.set_variable(rffi.cast(rffi.INT, l_param), List(argv))

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
                    incoming_blocks = []
                    for i in range(instruction.count_incoming):
                        l_block = llwrap.LLVMGetIncomingBlock(instruction.l_instr, i)
                        w_block = self.get_block(l_block)
                        incoming_blocks.append(w_block)
                    instruction.incoming_blocks = incoming_blocks[:]
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

class W_RetInstruction(W_BaseInstruction):

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        if len(self.operands) == 0:
            return NoValue()
        else:
            return args[0]

class W_BrInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a 'br' instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)
        self.w_bb_uncond = None

    def execute(self, args):
        return BasicBlock(self.w_bb_uncond)

class W_ConditionalInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a conditional
        'br' instruction. '''

    _immutable_fields_ = ['condition', 'w_bb_true', 'w_bb_false']

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)
        self.condition = _get_variable_wrapper(llwrap.LLVMGetCondition(l_instr))

    def execute(self, args):
        condition_var = args[0]
        assert isinstance(condition_var, Integer)
        if condition_var.value == True:
            return BasicBlock(self.w_bb_true)
        else:
            return BasicBlock(self.w_bb_false)

class W_ICmpInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'icmp'
        instruction. '''

    _immutable_fields_ = ['icmp_predicate']

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)
        self.icmp_predicate = llwrap.LLVMGetICmpPredicate(l_instr)

    def eval_condition(self, val1, val2):
        ''' Returns the wrapped boolean result of the comparison of the values of
            the two arguments, according to an ICmp predicate. '''

        assert isinstance(val1, Integer) and isinstance(val2, Integer)
        if self.icmp_predicate == llwrap.LLVMIntSLT:
            return Integer(val1.value < val2.value)
        elif self.icmp_predicate == llwrap.LLVMIntSLE:
            return Integer(val1.value <= val2.value)
        elif self.icmp_predicate == llwrap.LLVMIntEQ:
            return Integer(val1.value == val2.value)
        elif self.icmp_predicate == llwrap.LLVMIntNE:
            return Integer(val1.value != val2.value)
        elif self.icmp_predicate == llwrap.LLVMIntSGT:
            return Integer(val1.value > val2.value)
        elif self.icmp_predicate == llwrap.LLVMIntSGE:
            return Integer(val1.value >= val2.value)
        else:
            interpreter.exit_not_implemented("Unknown ICmp predicate %d" %\
                                             self.icmp_predicate)

    def execute(self, args):
        return self.eval_condition(args[0], args[1])

class W_PhiInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a 'phi'
        instruction. '''

    _immutable_fields_ = ['l_instr', 'count_incoming', 'incoming_blocks[*]',
                          'incoming_value[*]']

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)
        self.l_instr = l_instr
        self.count_incoming = llwrap.LLVMCountIncoming(l_instr)
        self.incoming_blocks = None
        incoming_value = []
        for i in range(self.count_incoming):
            wrapped_var = _get_variable_wrapper(llwrap.LLVMGetIncomingValue(l_instr, i))
            incoming_value.append(wrapped_var)
        self.incoming_value = incoming_value[:]

    @jit.unroll_safe
    def execute(self, args):
        ''' Returns the result of a given phi instruction. '''

        for i in range(self.count_incoming):
            w_block = self.incoming_blocks[i]
            if w_block == interpreter.Interpreter.interp_state.last_block:
                return interpreter.Interpreter.interp_state.lookup_var(self.incoming_value[i])
        raise MissingPredecessorBasicBlockException(self.name)

class W_CallInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a 'call'
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

    def execute(self, args):
        interp_state = interpreter.Interpreter.interp_state
        if interp_state.module.has_function(self.operands[-1].l_value):
            # the function is defined in the file being interpreted
            from state import Frame
            frame = Frame()
            for index in range(self.func_param_count):
                param = self.l_func_params[index]
                variable = interp_state.lookup_var(self.operands[index])
                frame.set_variable(param.addr, variable)
            func = interp_state.module.get_function(self.operands[-1].l_value)
            interp_fun = interpreter.Interpreter(module=interp_state.module,\
                                                 global_frame=interp_state.global_frame,\
                                                 frame=frame)
            result = interp_fun.run(func)
            return result
        else:
            # the function is not defined in the file being interpreted
            # XXX currently assuming it is printf or puts
            str_var = interp_state.lookup_var(self.string_format_ref)
            assert isinstance(str_var, String)
            string_format = str_var.value
            if self.func_name == "printf" or self.func_name == "puts":
                printf_args = []
                for i in range(1, len(self.operands) - 1):
                    var = interp_state.lookup_var(self.operands[i])
                    printf_args.append(var)
                interpreter.print_function(string_format, printf_args)
            else:
                interpreter.exit_not_implemented(self.func_name)
        return NoValue()

class W_SwitchInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a 'switch'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)
        self.default_branch = None
        self.w_blocks = None

    def get_switch_block(self, args):
        ''' Returns the block a switch instruction branches to. '''

        cond = args[0]
        assert isinstance(cond, Integer)
        for i in range(2, len(args), 2):
            switch_var = args[i]
            assert isinstance(switch_var, Integer)
            if cond.value == switch_var.value:
                return BasicBlock(self.w_blocks[i / 2  - 1])
        return BasicBlock(self.default_branch)

    def execute(self, args):
        return self.get_switch_block(args)

class W_SelectInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a 'select'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        cond = args[0]
        assert isinstance(cond, Integer)
        if cond.value:
            return args[1]
        else:
            return args[2]

class W_AddInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'add'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        x, y = args
        assert isinstance(x, Integer) and isinstance(y, Integer)
        return Integer(x.value + y.value)

class W_FAddInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'fadd'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        x, y = args
        assert isinstance(x, Float) and isinstance(y, Float)
        return Float(x.value + y.value)

class W_MulInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a 'mul'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        x, y = args
        assert isinstance(x, Integer) and isinstance(y, Integer)
        return Integer(x.value * y.value)

class W_FMulInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'fmul'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        x, y = args
        assert isinstance(x, Float) and isinstance(y, Float)
        return Float(x.value * y.value)

class W_SubInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a 'sub'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        x, y = args
        assert isinstance(x, Integer) and isinstance(y, Integer)
        return Integer(x.value - y.value)

class W_FSubInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'fsub'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        x, y = args
        assert isinstance(x, Float) and isinstance(y, Float)
        return Float(x.value - y.value)

class W_SDivInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'sdiv'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        x, y = args
        assert isinstance(x, Integer) and isinstance(y, Integer)
        return Integer(x.value / y.value)

class W_FDivInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'fdiv'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        x, y = args
        assert isinstance(x, Float) and isinstance(y, Float)
        return Float(x.value / y.value)

class W_SRemInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'srem'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        x, y = args
        assert isinstance(x, Integer) and isinstance(y, Integer)
        return Integer(int(x.value) % int(y.value))

class W_AndInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'and'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        x, y = args
        assert isinstance(x, Integer) and isinstance(y, Integer)
        return Integer(int(x.value) & int(y.value))

class W_OrInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'or'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        x, y = args
        assert isinstance(x, Integer) and isinstance(y, Integer)
        return Integer(int(x.value) | int(y.value))

class W_XorInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'xor'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        x, y = args
        assert isinstance(x, Integer) and isinstance(y, Integer)
        return Integer(int(x.value) ^ int(y.value))

class W_ShlInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'shl'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        x, y = args
        assert isinstance(x, Integer) and isinstance(y, Integer)
        return Integer(int(x.value) << int(y.value))

class W_AllocaInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'alloca'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        return Ptr(lltype.scoped_alloc(rffi.VOIDP.TO, 1))

class W_LoadInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a 'load'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        return args[0]

class W_FPExtInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'fpext'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        # extend a floating point value (eg float -> double)
        x = args[0]
        assert isinstance(x, Float)
        return Float(x.value)


class W_FPTruncInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is an 'fptrunc'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        # truncate a floating point value (double -> float)
        x = args[0]
        assert isinstance(x, Float)
        return Float(x.value)

class W_ZExtInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a 'zext'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        x = args[0]
        assert isinstance(x, Integer)
        return Integer(x.value)

class W_SIToFPInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a 'sitofp'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        # convert Signed to Floating Point
        x = args[0]
        assert isinstance(x, Integer)
        return Float(float(x.value))

class W_StoreInstruction(W_BaseInstruction):
    ''' Represents a wrapper for an LLVMValueRef that is a 'sitofp'
        instruction. '''

    def __init__(self, l_instr, w_module):
        W_BaseInstruction.__init__(self, l_instr, w_module)

    def execute(self, args):
        var = interpreter.Interpreter.interp_state.lookup_var(self.operands[0])
        interpreter.Interpreter.interp_state.set_var(self.operands[1].l_value, var)
        return NoValue()

def _get_instruction(opcode, l_instruction, w_module):
    ''' Returns the appropriate wrapper for the specified instruction. '''

    if opcode == llwrap.LLVMRet:
        return W_RetInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMBr:
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
    elif opcode == llwrap.LLVMSelect:
        return W_SelectInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMAdd:
        return W_AddInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMFAdd:
        return W_FAddInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMMul:
        return W_MulInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMFMul:
        return W_FMulInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMSub:
        return W_SubInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMFSub:
        return W_FSubInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMSDiv:
        return W_SDivInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMFDiv:
        return W_FDivInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMSRem:
        return W_SRemInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMAnd:
        return W_AndInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMOr:
        return W_OrInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMXor:
        return W_XorInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMShl:
        return W_ShlInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMAlloca:
        return W_AllocaInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMLoad:
        return W_LoadInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMFPExt:
        return W_FPExtInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMZExt:
        return W_ZExtInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMFPTrunc:
        return W_FPTruncInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMSIToFP:
        return W_SIToFPInstruction(l_instruction, w_module)
    elif opcode == llwrap.LLVMStore:
        return W_StoreInstruction(l_instruction, w_module)
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
    ''' Represents a variable that is an LLVM constant. '''

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
