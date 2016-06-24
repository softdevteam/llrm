from __future__ import with_statement

from interpreter import Interpreter
from state import State
from type_wrapper import Integer, List, String, NumericType
from llvm_wrapper import *

import sys
import subprocess

class InterpreterPlaceholder(Interpreter):

    def __init__(self):
        pass

    def puts(self, string, args=[]):
        self.output.append(string)
        for arg in args:
            if isinstance(arg, NumericType):
                self.output.append(str(arg.value))
            else:
                self.output.append(str(arg))

    def set_args(self, main_fun, global_state, argc, argv):
        for index in range(0, LLVMCountParams(main_fun)):
            param = LLVMGetParam(main_fun, index)
            if index == 0:
                global_state.set_variable(rffi.cast(rffi.INT, param),\
                                                    Integer(argc))
            else:
                global_state.set_variable(rffi.cast(rffi.INT, param),\
                                                    List(argv))

    def setup_interp(self, filename, argc, argv):
        self.output = []
        module = LLVMModuleCreateWithName("test_module")

        with lltype.scoped_alloc(rffi.CCHARPP.TO, 1) as out_message:
            mem_buff = lltype.malloc(rffi.VOIDP.TO, 1, flavor="raw")
            with lltype.scoped_alloc(rffi.VOIDPP.TO, 1) as mem_buff_ptr:
                mem_buff_ptr[0] = mem_buff
                rc = LLVMCreateMemoryBufferWithContentsOfFile(filename, mem_buff_ptr, out_message)
                assert rc == 0
                mem_buff = mem_buff_ptr[0]

            with lltype.scoped_alloc(rffi.VOIDPP.TO, 1) as module_ptr:
                module_ptr[0] = module
                rc = LLVMParseBitcode(mem_buff, module_ptr, out_message)
                assert rc == 0
                module = module_ptr[0]
            main_fun = LLVMGetNamedFunction(module, "main")

        with lltype.scoped_alloc(rffi.VOIDPP.TO, 1) as basic_blocks_main_ptr:
            LLVMGetBasicBlocks(main_fun, basic_blocks_main_ptr)
            basic_blocks_main = basic_blocks_main_ptr[0]

        global_state = State()
        global_var = LLVMGetFirstGlobal(module)

        while global_var:
            with lltype.scoped_alloc(rffi.INTP.TO, 1) as int_ptr:
                initializer = LLVMGetInitializer(global_var)
                assert LLVMIsConstantString(initializer)
                string_var = LLVMGetAsString(initializer, int_ptr)
                global_state.set_variable(rffi.cast(rffi.INT, global_var),\
                                          String(rffi.charp2str(string_var)))
            global_var = LLVMGetNextGlobal(global_var)

        functions = {}
        function = LLVMGetFirstFunction(module)
        while function:
            if not LLVMIsDeclaration(function):
                functions[rffi.cast(rffi.INT, function)] = function
            function = LLVMGetNextFunction(function)
        self.set_args(main_fun, global_state, argc, argv)
        return (module, global_state, functions, main_fun)

    def run_bytecode(self, argc, argv, bytecode):
        # need functions, global_state
        with open("temp.ll", "w+") as f:
            f.write(bytecode)
        command = "llvm-as temp.ll"
        subprocess.call(command, shell=True)
        (module, global_state, functions, main_fun) = self.setup_interp("temp.bc", argc, argv)
        self.global_state = global_state
        self.functions = functions
        self.run(main_fun)
        return self.output

def test_bytecode01():
    interp = InterpreterPlaceholder()
    argc = 2
    argv = ["temp.bc", "another arg"]
    result = interp.run_bytecode(argc, argv, """
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.1 = private unnamed_addr constant [43 x i8] c"c is %d and argc is %d and argc + 1 is %d\0A\00", align 1
@.str.2 = private unnamed_addr constant [12 x i8] c"argc is %d\0A\00", align 1
@.str.3 = private unnamed_addr constant [15 x i8] c"a float is %f\0A\00", align 1
@.str.4 = private unnamed_addr constant [20 x i8] c"5 * argc + 1 is %d\0A\00", align 1
@str = private unnamed_addr constant [6 x i8] c"hello\00"

; Function Attrs: nounwind uwtable
define i32 @main(i32 %argc, i8** nocapture readnone %argv) #0 {
entry:
%puts = tail call i32 @puts(i8* getelementptr inbounds ([6 x i8], [6 x i8]* @str, i64 0, i64 0))
%add2 = add nsw i32 %argc, 1
%call3 = tail call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([43 x i8], [43 x i8]* @.str.1, i64 0, i64 0), i32 133, i32 %argc, i32 %add2)
%call4 = tail call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([12 x i8], [12 x i8]* @.str.2, i64 0, i64 0), i32 %argc)
%call5 = tail call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([15 x i8], [15 x i8]* @.str.3, i64 0, i64 0), double 2.500000e+00)
%mul = mul nsw i32 %argc, 5
%add6 = add nsw i32 %mul, 1
%call7 = tail call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([20 x i8], [20 x i8]* @.str.4, i64 0, i64 0), i32 %add6)
ret i32 0
}

; Function Attrs: nounwind
declare i32 @printf(i8* nocapture readonly, ...) #1

; Function Attrs: nounwind
declare i32 @puts(i8* nocapture) #2

attributes #0 = { nounwind uwtable "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { nounwind "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #2 = { nounwind }

!llvm.ident = !{!0}

!0 = !{!"clang version 3.8.0 (tags/RELEASE_380/final)"}
""")
    assert result[0] == "hello"
    assert result[1] == "c is %d and argc is %d and argc + 1 is %d\n"
    assert result[2] == "133"
    assert result[3] == str(argc)
    assert result[4] == str(argc + 1)
    assert result[5] == "argc is %d\n"
    assert result[8] == "2.5"


