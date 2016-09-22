from state import State
from type_wrapper import NumericValue

import interpreter
import subprocess

class BaseBytecodeTest(interpreter.Interpreter):

    def __init__(self):
        self.last_block = None

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
        module.load_globals(global_state, argc, argv)
        return (module, global_state)

    def run_bytecode(self, argc, argv, bytecode):
        # need functions, global_state
        with open("temp.ll", "w") as f:
            f.write(bytecode)
        command = "llvm-as temp.ll"
        rc = subprocess.call(command, shell=True)
        assert rc == 0
        (module, global_state) = self.setup_interp("temp.bc", argc, argv)
        self.module = module
        self.global_state = global_state
        interpreter.Interpreter.interp_state.update(module=module, global_state=global_state)
        interpreter.print_function = self.puts
        self.run(module.w_main_fun)
        return self.output
