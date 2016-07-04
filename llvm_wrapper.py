from subprocess import Popen, PIPE

from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rtyper.tool import rffi_platform
from rpython.translator.tool.cbuild import ExternalCompilationInfo

class CConfig(object):
    _includes = "llvm-c/Core.h llvm-c/BitReader.h"
    libs = Popen("llvm-config --libs core native --system-libs",
                  shell=True, stdout=PIPE, stderr=PIPE).communicate()[0].split()
    c_flags = Popen("llvm-config --cflags",
                    shell=True, stdout=PIPE, stderr=PIPE).communicate()[0].split()
    ld_flags = Popen("llvm-config --cxxflags --ldflags",
                     shell=True, stdout=PIPE, stderr=PIPE).communicate()[0].split()

    c_flags = [flag for flag in c_flags if flag != "-pedantic"]
    c_flags.extend(["-g"])
    ld_flags.append("-lclang")

    # remove -l from each library
    libs = [lib[2:] for lib in libs]

    _compilation_info_ = ExternalCompilationInfo(includes=_includes.split(),
                                                 library_dirs=["/usr/local/lib"],
                                                 libraries=libs,
                                                 compile_extra=c_flags,
                                                 link_extra=ld_flags)
types_string = '''
LLVMVoidTypeKind
LLVMHalfTypeKind
LLVMFloatTypeKind
LLVMDoubleTypeKind
LLVMX86_FP80TypeKind
LLVMFP128TypeKind
LLVMPPC_FP128TypeKind
LLVMLabelTypeKind
LLVMIntegerTypeKind
LLVMFunctionTypeKind
LLVMStructTypeKind
LLVMArrayTypeKind
LLVMPointerTypeKind
LLVMVectorTypeKind
LLVMMetadataTypeKind
LLVMX86_MMXTypeKind
LLVMTokenTypeKind'''

opcodes_string ='''
LLVMRet
LLVMBr
LLVMSwitch
LLVMIndirectBr
LLVMInvoke
LLVMUnreachable
LLVMAdd
LLVMFAdd
LLVMSub
LLVMFSub
LLVMMul
LLVMFMul
LLVMUDiv
LLVMSDiv
LLVMFDiv
LLVMURem
LLVMSRem
LLVMFRem
LLVMShl
LLVMLShr
LLVMAShr
LLVMAnd
LLVMOr
LLVMXor
LLVMAlloca
LLVMLoad
LLVMStore
LLVMGetElementPtr
LLVMTrunc
LLVMZExt
LLVMSExt
LLVMFPToUI
LLVMFPToSI
LLVMUIToFP
LLVMSIToFP
LLVMFPTrunc
LLVMFPExt
LLVMPtrToInt
LLVMIntToPtr
LLVMBitCast
LLVMAddrSpaceCast
LLVMICmp
LLVMFCmp
LLVMPHI
LLVMCall
LLVMSelect
LLVMUserOp1
LLVMUserOp2
LLVMVAArg
LLVMExtractElement
LLVMInsertElement
LLVMShuffleVector
LLVMExtractValue
LLVMInsertValue
LLVMFence
LLVMAtomicCmpXchg
LLVMAtomicRMW
LLVMResume
LLVMLandingPad
LLVMCleanupRet
LLVMCatchRet
LLVMCatchPad
LLVMCleanupPad
LLVMCatchSwitch'''

int_predicate_string = '''
LLVMIntEQ
LLVMIntNE
LLVMIntUGT
LLVMIntUGE
LLVMIntULT
LLVMIntULE
LLVMIntSGT
LLVMIntSGE
LLVMIntSLT
LLVMIntSLE '''

real_predicate_string = '''
LLVMRealPredicateFalse
LLVMRealOEQ
LLVMRealOGT
LLVMRealOGE
LLVMRealOLT
LLVMRealOLE
LLVMRealONE
LLVMRealORD
LLVMRealUNO
LLVMRealUEQ
LLVMRealUGT
LLVMRealUGE
LLVMRealULT
LLVMRealULE
LLVMRealUNE
LLVMRealPredicateTrue
'''

ops = opcodes_string.split()

for cmd in ops:
    setattr(CConfig, cmd, rffi_platform.ConstantInteger(cmd))

types = types_string.split()

for llvm_type in types:
    setattr(CConfig, llvm_type, rffi_platform.ConstantInteger(llvm_type))

int_predicates = int_predicate_string.split()

for pred in int_predicates:
    setattr(CConfig, pred, rffi_platform.ConstantInteger(pred))

real_predicates = real_predicate_string.split()

for pred in real_predicates:
    setattr(CConfig, pred, rffi_platform.ConstantInteger(pred))

cconfig = rffi_platform.configure(CConfig)

for cmd in ops:
    globals()[cmd] = cconfig[cmd]

for llvm_type in types:
    globals()[llvm_type] = cconfig[llvm_type]

for pred in int_predicates:
    globals()[pred] = cconfig[pred]

for pred in real_predicates:
    globals()[pred] = cconfig[pred]


LLVMModuleCreateWithName = rffi.llexternal("LLVMModuleCreateWithName",
                                           [rffi.CCHARP],
                                            rffi.VOIDP,
                                            compilation_info=CConfig._compilation_info_)

LLVMPrintModuleToString = rffi.llexternal("LLVMPrintModuleToString",
                                          [rffi.VOIDP],
                                           rffi.CCHARP,
                                           compilation_info=CConfig._compilation_info_)

LLVMPrintValueToString = rffi.llexternal("LLVMPrintValueToString",
                                         [rffi.VOIDP],
                                          rffi.CCHARP,
                                          compilation_info=CConfig._compilation_info_)

LLVMPrintTypeToString = rffi.llexternal("LLVMPrintTypeToString",
                                         [rffi.VOIDP],
                                          rffi.CCHARP,
                                          compilation_info=CConfig._compilation_info_)

LLVMCreateMemoryBufferWithContentsOfFile = rffi.llexternal("LLVMCreateMemoryBufferWithContentsOfFile",
                                                            [rffi.CCHARP, rffi.VOIDPP, rffi.CCHARPP],
                                                            rffi.INT,
                                                            compilation_info=CConfig._compilation_info_)

LLVMParseBitcode = rffi.llexternal("LLVMParseBitcode",
                                   [rffi.VOIDP, rffi.VOIDPP, rffi.CCHARPP],
                                    rffi.INT,
                                    compilation_info=CConfig._compilation_info_)

LLVMGetNamedFunction = rffi.llexternal("LLVMGetNamedFunction",
                                       [rffi.VOIDP, rffi.CCHARP],
                                        rffi.VOIDP,
                                        compilation_info=CConfig._compilation_info_)

LLVMGetBasicBlocks = rffi.llexternal("LLVMGetBasicBlocks",
                                     [rffi.VOIDP, rffi.VOIDPP],
                                      lltype.Void,
                                      compilation_info=CConfig._compilation_info_)

LLVMGetValueName = rffi.llexternal("LLVMGetValueName",
                                   [rffi.VOIDP],
                                    rffi.CCHARP,
                                    compilation_info=CConfig._compilation_info_)

LLVMGetFirstBasicBlock = rffi.llexternal("LLVMGetFirstBasicBlock",
                                         [rffi.VOIDP],
                                          rffi.VOIDP,
                                          compilation_info=CConfig._compilation_info_)

LLVMGetNextBasicBlock = rffi.llexternal("LLVMGetNextBasicBlock",
                                        [rffi.VOIDP],
                                         rffi.VOIDP,
                                         compilation_info=CConfig._compilation_info_)

LLVMGetFirstInstruction = rffi.llexternal("LLVMGetFirstInstruction",
                                          [rffi.VOIDP],
                                           rffi.VOIDP,
                                           compilation_info=CConfig._compilation_info_)

LLVMGetNextInstruction = rffi.llexternal("LLVMGetNextInstruction",
                                         [rffi.VOIDP],
                                          rffi.VOIDP,
                                          compilation_info=CConfig._compilation_info_)

LLVMGetNumOperands = rffi.llexternal("LLVMGetNumOperands",
                                     [rffi.VOIDP],
                                      rffi.INT,
                                      compilation_info=CConfig._compilation_info_)

LLVMGetInstructionOpcode = rffi.llexternal("LLVMGetInstructionOpcode",
                                           [rffi.VOIDP],
                                            rffi.INT,
                                            compilation_info=CConfig._compilation_info_)

LLVMGetOperand = rffi.llexternal("LLVMGetOperand",
                                 [rffi.VOIDP, lltype.Unsigned],
                                  rffi.VOIDP,
                                  compilation_info=CConfig._compilation_info_)

LLVMIsConstant = rffi.llexternal("LLVMIsConstant",
                                 [rffi.VOIDP],
                                  rffi.INT,
                                  compilation_info=CConfig._compilation_info_)

LLVMConstIntGetSExtValue = rffi.llexternal("LLVMConstIntGetSExtValue",
                                           [rffi.VOIDP],
                                            rffi.INT,
                                            compilation_info=CConfig._compilation_info_)

LLVMConstIntGetZExtValue = rffi.llexternal("LLVMConstIntGetZExtValue",
                                           [rffi.VOIDP],
                                            rffi.INT,
                                            compilation_info=CConfig._compilation_info_)

LLVMGetValueName = rffi.llexternal("LLVMGetValueName",
                                   [rffi.VOIDP],
                                    rffi.CCHARP,
                                    compilation_info=CConfig._compilation_info_)

LLVMGetFirstGlobal = rffi.llexternal("LLVMGetFirstGlobal",
                                     [rffi.VOIDP],
                                      rffi.VOIDP,
                                      compilation_info=CConfig._compilation_info_)

LLVMGetNextGlobal = rffi.llexternal("LLVMGetNextGlobal",
                                     [rffi.VOIDP],
                                      rffi.VOIDP,
                                      compilation_info=CConfig._compilation_info_)

LLVMGetInitializer = rffi.llexternal("LLVMGetInitializer",
                                     [rffi.VOIDP],
                                      rffi.VOIDP,
                                      compilation_info=CConfig._compilation_info_)

LLVMIsGlobalConstant = rffi.llexternal("LLVMIsGlobalConstant",
                                       [rffi.VOIDP],
                                        rffi.INT,
                                        compilation_info=CConfig._compilation_info_)

LLVMIsConstantString = rffi.llexternal("LLVMIsConstantString",
                                       [rffi.VOIDP],
                                        rffi.INT,
                                        compilation_info=CConfig._compilation_info_)

LLVMGetAsString = rffi.llexternal("LLVMGetAsString",
                                  [rffi.VOIDP, rffi.INTP],
                                   rffi.CCHARP,
                                   compilation_info=CConfig._compilation_info_)

LLVMGetParam = rffi.llexternal("LLVMGetParam",
                               [rffi.VOIDP, rffi.INT],
                                rffi.VOIDP,
                                compilation_info=CConfig._compilation_info_)

LLVMCountParams = rffi.llexternal("LLVMCountParams",
                                  [rffi.VOIDP],
                                   rffi.INT,
                                   compilation_info=CConfig._compilation_info_)

LLVMGetFirstFunction = rffi.llexternal("LLVMGetFirstFunction",
                                       [rffi.VOIDP],
                                        rffi.VOIDP,
                                        compilation_info=CConfig._compilation_info_)

LLVMGetNextFunction = rffi.llexternal("LLVMGetNextFunction",
                                       [rffi.VOIDP],
                                        rffi.VOIDP,
                                        compilation_info=CConfig._compilation_info_)

LLVMIsDeclaration = rffi.llexternal("LLVMIsDeclaration",
                                    [rffi.VOIDP],
                                     rffi.INT,
                                     compilation_info=CConfig._compilation_info_)

LLVMConstInt = rffi.llexternal("LLVMConstInt",
                               [rffi.VOIDP, rffi.INT, rffi.INT],
                                rffi.VOIDP,
                                compilation_info=CConfig._compilation_info_)

LLVMConstRealGetDouble = rffi.llexternal("LLVMConstRealGetDouble",
                                         [rffi.VOIDP, rffi.SIGNEDP],
                                          rffi.DOUBLE,
                                          compilation_info=CConfig._compilation_info_)

LLVMGetTypeKind = rffi.llexternal("LLVMGetTypeKind",
                                  [rffi.VOIDP],
                                   rffi.INT,
                                   compilation_info=CConfig._compilation_info_)

LLVMTypeOf = rffi.llexternal("LLVMTypeOf",
                             [rffi.VOIDP],
                              rffi.VOIDP,
                              compilation_info=CConfig._compilation_info_)

LLVMValueAsBasicBlock = rffi.llexternal("LLVMValueAsBasicBlock",
                                         [rffi.VOIDP],
                                          rffi.VOIDP,
                                          compilation_info=CConfig._compilation_info_)

LLVMGetCondition = rffi.llexternal("LLVMGetCondition",
                                   [rffi.VOIDP],
                                    rffi.VOIDP,
                                    compilation_info=CConfig._compilation_info_)

LLVMIsConditional = rffi.llexternal("LLVMIsConditional",
                                    [rffi.VOIDP],
                                     rffi.VOIDP,
                                     compilation_info=CConfig._compilation_info_)

LLVMGetICmpPredicate = rffi.llexternal("LLVMGetICmpPredicate",
                                       [rffi.VOIDP],
                                        rffi.INT,
                                        compilation_info=CConfig._compilation_info_)

LLVMGetFCmpPredicate = rffi.llexternal("LLVMGetFCmpPredicate",
                                       [rffi.VOIDP],
                                        rffi.INT,
                                        compilation_info=CConfig._compilation_info_)

LLVMCountIncoming = rffi.llexternal("LLVMCountIncoming",
                                    [rffi.VOIDP],
                                     rffi.INT,
                                     compilation_info=CConfig._compilation_info_)

LLVMGetIncomingValue = rffi.llexternal("LLVMGetIncomingValue",
                                       [rffi.VOIDP, rffi.INT],
                                        rffi.VOIDP,
                                        compilation_info=CConfig._compilation_info_)

LLVMGetIncomingBlock = rffi.llexternal("LLVMGetIncomingBlock",
                                       [rffi.VOIDP, rffi.INT],
                                        rffi.VOIDP,
                                        compilation_info=CConfig._compilation_info_)

LLVMGetNumSuccessors = rffi.llexternal("LLVMGetNumSuccessors",
                                       [rffi.VOIDP],
                                        rffi.INT,
                                        compilation_info=CConfig._compilation_info_)

LLVMGetSuccessor = rffi.llexternal("LLVMGetSuccessor",
                                   [rffi.VOIDP, rffi.INT],
                                    rffi.VOIDP,
                                    compilation_info=CConfig._compilation_info_)

LLVMGetSwitchDefaultDest = rffi.llexternal("LLVMGetSwitchDefaultDest",
                                           [rffi.VOIDP],
                                            rffi.VOIDP,
                                            compilation_info=CConfig._compilation_info_)

LLVMIsUndef = rffi.llexternal("LLVMIsUndef",
                              [rffi.VOIDP],
                               rffi.INT,
                               compilation_info=CConfig._compilation_info_)

class W_Module(object):

    def __init__(self, l_module):
        from state import State
        self.constants = State()
        self.l_module = l_module
        self.w_functions = self.get_functions()
        self.w_main_fun = W_Function(LLVMGetNamedFunction(l_module, "main"), self)

    def get_functions(self):
        l_func = LLVMGetFirstFunction(self.l_module)
        w_functions = {}  # although maybe actually a dict? list for now?
        while l_func:
            if not LLVMIsDeclaration(l_func):
                # we only want functioned defined internally
                w_functions[rffi.cast(rffi.INT, l_func)] = W_Function(l_func, self)
            l_func = LLVMGetNextFunction(l_func)
        return w_functions

    def load_globals(self, global_state, main_argc, main_argv):

        l_global_var = LLVMGetFirstGlobal(self.l_module)
        l_main_fun = LLVMGetNamedFunction(self.l_module, "main")
        while l_global_var:
            #print "GLOBAL VAR", rffi.charp2str(LLVMPrintValueToString(l_global_var))
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
        self.w_blocks = self.get_blocks(l_function, w_module)

    def get_blocks(self, l_function, w_module):
        l_block = LLVMGetFirstBasicBlock(l_function)
        w_blocks = []
        self.w_block_dict = {}
        prev = None
        while l_block:
            current_block = W_Block(l_block, w_module)
            if prev:
                prev.w_next_block = current_block
            prev = current_block
            self.w_block_dict[rffi.cast(rffi.INT, l_block)] = current_block
            w_blocks.append(current_block)
            l_block = LLVMGetNextBasicBlock(l_block)
        return w_blocks

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
            #self.l_function = None
            if not LLVMIsDeclaration(self.l_operands[-1]):
                self.l_function = self.l_operands[-1]
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


