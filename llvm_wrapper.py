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

ops = opcodes_string.split()

for cmd in ops:
    setattr(CConfig, cmd, rffi_platform.ConstantInteger(cmd))

cconfig = rffi_platform.configure(CConfig)

for cmd in ops:
    globals()[cmd] = cconfig[cmd]

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

def getReference():
    return lltype.malloc(rffi.VOIDP.TO, 1, flavor="raw")
