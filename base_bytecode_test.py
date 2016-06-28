from state import State
from type_wrapper import Integer, List, String, NumericValue
from llvm_wrapper import *

import interpreter
import sys
import subprocess

class BaseBytecodeTest(interpreter.Interpreter):

    def __init__(self):
        pass

    def puts(self, string, args=[]):
        self.output.append(string)
        for arg in args:
            if isinstance(arg, NumericValue):
                self.output.append(str(arg.value))
            else:
                self.output.append(str(arg))

    def setup_interp(self, filename, argc, argv):
        self.output = []
        module = interpreter.create_module(filename)
        global_state = State()
        interpreter.load_globals(module, global_state, argc, argv)
        functions = interpreter.load_func_table(module)
        main_fun = LLVMGetNamedFunction(module, "main")
        return (module, global_state, functions, main_fun)

    def run_bytecode(self, argc, argv, bytecode):
        # need functions, global_state
        with open("temp.ll", "w") as f:
            f.write(bytecode)
        command = "llvm-as temp.ll"
        rc = subprocess.call(command, shell=True)
        assert rc == 0
        (module, global_state, functions, main_fun) = self.setup_interp("temp.bc", argc, argv)
        self.global_state = global_state
        self.functions = functions
        self.run(main_fun)
        return self.output
