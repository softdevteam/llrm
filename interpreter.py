from __future__ import with_statement
from rpython.rlib import jit
from type_wrapper import NoValue, NumericValue, BasicBlock
from state import State, InterpreterState
from rpython.rtyper.lltypesystem import rffi, lltype

import llvm_wrapper as llwrap
import llvm_objects
import sys

def target(*args):
    return main, None

def jitpolicy(driver):
    from rpython.jit.codewriter.policy import JitPolicy
    return JitPolicy()

def get_printable_location(interpreter, block, function):
    return "%s: %s" % (function.name, interpreter.current_instruction.name)

jit_driver = jit.JitDriver(greens=["self", "block", "function"],
                           reds=[],
                           get_printable_location=get_printable_location)

class InvalidFileException(Exception):
    pass

class UnparsableBitcodeException(Exception):
    pass

def exit_not_implemented(name):
    print "[ERROR]: Found unimplemented operation. Exiting."
    raise NotImplementedError(name)

def puts(string, args=[]):
    ''' Prints (on separate lines) the given string and the arguments
        specified. '''

    print string
    if args:
        for arg in args:
            assert isinstance(arg, NumericValue)
            print arg.value
        print "\n\n"

# the print function to use - can be changed to some other function
# for testing purposes (to supress and save the output)
print_function = puts

class Interpreter(object):

    interp_state = InterpreterState()

    def __init__(self, module, global_state):
        self.module = module
        self.global_state = global_state
        self.current_instruction = None
        Interpreter.interp_state.update(module=self.module,\
                                        global_state=self.global_state)

    @jit.unroll_safe
    def _get_args(self, args):
        ''' Returns a list of Values representing each Variable
            in args. '''

        arg_vals = []
        for arg in args:
            arg_vals.append(self.interp_state.lookup_var(arg, ignore_err=True))
        return arg_vals

    def run(self, function):
        ''' Runs each instruction of the given function and creates
            a new stack frame for the local variables. '''

        self.frame = State()
        block = function.get_first_block()
        Interpreter.interp_state.update(frame=self.frame, last_block=block)
        while block:
            jit_driver.jit_merge_point(function=function, block=block, self=self)
            instruction = block.get_first_instruction()
            next_block = block.w_next_block
            while instruction:
                self.current_instruction = instruction
                result = instruction.execute(self._get_args(instruction.operands))
                Interpreter.interp_state.update(frame=self.frame)
                if isinstance(result, BasicBlock):
                    next_block = result.value
                    break
                elif not isinstance(result, NoValue):
                    self.frame.set_variable(instruction.addr, result)
                instruction = instruction.w_next_instr
                # last instruction should be ret
                if not instruction:
                    return result
            self.interp_state.update(last_block=block)
            block = next_block

def create_module(filename):
    ''' Returns the W_Module representing an LLVM module created with the
        contents of the given file. '''

    module = llwrap.LLVMModuleCreateWithName("module")
    with lltype.scoped_alloc(rffi.CCHARPP.TO, 1) as out_message:
        with lltype.scoped_alloc(rffi.VOIDP.TO, 1) as mem_buff:
            with lltype.scoped_alloc(rffi.VOIDPP.TO, 1) as mem_buff_ptr:
                mem_buff_ptr[0] = mem_buff
                rc = llwrap.LLVMCreateMemoryBufferWithContentsOfFile(filename,
                                                                     mem_buff_ptr,
                                                                     out_message)
                if rc != 0:
                    print "[ERROR]: Cannot create memory buffer with contents of"\
                          " %s: %s.\n" % (filename, rffi.charp2str(out_message[0]))
                    raise InvalidFileException(filename)
                mem_buff = mem_buff_ptr[0]
            with lltype.scoped_alloc(rffi.VOIDPP.TO, 1) as module_ptr:
                module_ptr[0] = module
                rc = llwrap.LLVMParseBitcode(mem_buff, module_ptr, out_message)
                if rc != 0:
                    print "[ERROR]: Cannot parse %s: %s.\n" % (filename,
                                                               rffi.charp2str(out_message[0]))
                    raise UnparsableBitcodeException(filename)
                module = module_ptr[0]
    return llvm_objects.W_Module(module)

def main(args):
    if len(args) < 2:
        print"[ERROR]: Need an argument:\nUsage: ./interpreter-c name.bc [C args]\n"
        return 1
    module = create_module(args[1])
    main_argc = len(args) - 1
    main_argv = args[1:]
    global_state = State()
    module.load_globals(global_state, main_argc, main_argv)
    interp = Interpreter(module, global_state)
    interp.run(module.w_main_fun)
    return 0

if __name__ == '__main__':
   main(sys.argv)
