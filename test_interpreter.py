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
        assert len(self.output) == 0
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

def test_arithmetic():
    interp = InterpreterPlaceholder()
    argc = 2
    argv = ["temp.bc", "another arg"]
    result = interp.run_bytecode(argc, argv, r"""
; ModuleID = 'test.bc'
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str = private unnamed_addr constant [43 x i8] c"c is %d and argc is %d and argc + 1 is %d\0A\00", align 1
@.str.1 = private unnamed_addr constant [12 x i8] c"argc is %d\0A\00", align 1
@.str.2 = private unnamed_addr constant [15 x i8] c"a float is %f\0A\00", align 1
@.str.3 = private unnamed_addr constant [20 x i8] c"5 * argc + 1 is %d\0A\00", align 1
@.str.4 = private unnamed_addr constant [6 x i8] c"hello\00", align 1

; Function Attrs: nounwind uwtable
define i32 @main(i32 %argc, i8** %argv) #0 {
entry:
  %retval = alloca i32, align 4
  %argc.addr = alloca i32, align 4
  %argv.addr = alloca i8**, align 8
  %c = alloca i32, align 4
  store i32 0, i32* %retval, align 4
  store i32 %argc, i32* %argc.addr, align 4
  store i8** %argv, i8*** %argv.addr, align 8
  store i32 133, i32* %c, align 4
  %0 = load i32, i32* %c, align 4
  %1 = load i32, i32* %argc.addr, align 4
  %2 = load i32, i32* %argc.addr, align 4
  %add = add nsw i32 %2, 1
  %call = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([43 x i8], [43 x i8]* @.str, i32 0, i32 0), i32 %0, i32 %1, i32 %add)
  %3 = load i32, i32* %argc.addr, align 4
  %call1 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([12 x i8], [12 x i8]* @.str.1, i32 0, i32 0), i32 %3)
  %call2 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([15 x i8], [15 x i8]* @.str.2, i32 0, i32 0), double 2.550000e+00)
  %4 = load i32, i32* %argc.addr, align 4
  %mul = mul nsw i32 5, %4
  %add3 = add nsw i32 %mul, 1
  %call4 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([20 x i8], [20 x i8]* @.str.3, i32 0, i32 0), i32 %add3)
  %call5 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([6 x i8], [6 x i8]* @.str.4, i32 0, i32 0))
  ret i32 0
}

declare i32 @printf(i8*, ...) #1

attributes #0 = { nounwind uwtable "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.ident = !{!0}

!0 = !{!"clang version 3.8.0 (tags/RELEASE_380/final)"}
""")

    assert result[0] == "c is %d and argc is %d and argc + 1 is %d\n"
    assert result[1] == "133"
    assert result[2] == str(argc)
    assert result[3] == str(argc + 1)
    assert result[4] == "argc is %d\n"
    assert result[5] == str(argc)
    assert result[6] == "a float is %f\n"
    assert result[7] == "2.55"
    assert result[8] == "5 * argc + 1 is %d\n"
    assert result[9] == str(5 * argc + 1)
    assert result[10] == "hello"

def test_functions():
    interp = InterpreterPlaceholder()
    argc = 4
    argv = ["temp.bc", "another arg", "3 args", "another"]
    result = interp.run_bytecode(argc, argv, r"""
; ModuleID = 'test.bc'
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str = private unnamed_addr constant [3 x i8] c"%d\00", align 1

; Function Attrs: nounwind uwtable
define i32 @sum(i32 %a, i32 %b) #0 {
entry:
  %a.addr = alloca i32, align 4
  %b.addr = alloca i32, align 4
  store i32 %a, i32* %a.addr, align 4
  store i32 %b, i32* %b.addr, align 4
  %0 = load i32, i32* %a.addr, align 4
  %1 = load i32, i32* %b.addr, align 4
  %add = add nsw i32 %0, %1
  ret i32 %add
}

; Function Attrs: nounwind uwtable
define i32 @main(i32 %argc, i8** %argv) #0 {
entry:
  %retval = alloca i32, align 4
  %argc.addr = alloca i32, align 4
  %argv.addr = alloca i8**, align 8
  store i32 0, i32* %retval, align 4
  store i32 %argc, i32* %argc.addr, align 4
  store i8** %argv, i8*** %argv.addr, align 8
  %0 = load i32, i32* %argc.addr, align 4
  %call = call i32 @sum(i32 %0, i32 13)
  %call1 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([3 x i8], [3 x i8]* @.str, i32 0, i32 0), i32 %call)
  ret i32 0
}

declare i32 @printf(i8*, ...) #1

attributes #0 = { nounwind uwtable "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.ident = !{!0}

!0 = !{!"clang version 3.8.0 (tags/RELEASE_380/final)"} """)

    assert result[0] == "%d"
    assert result[1] == "17"

def test_floats():
    interp = InterpreterPlaceholder()
    argc = 1
    argv = ["temp.bc"]
    result = interp.run_bytecode(argc, argv, r"""
; ModuleID = 'test.bc'
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str = private unnamed_addr constant [4 x i8] c"%d\0A\00", align 1
@.str.1 = private unnamed_addr constant [4 x i8] c"%f\0A\00", align 1
@.str.2 = private unnamed_addr constant [5 x i8] c"%lf\0A\00", align 1

; Function Attrs: nounwind uwtable
define float @sum_fl_int(double %a, i32 %b) #0 {
entry:
  %a.addr = alloca double, align 8
  %b.addr = alloca i32, align 4
  store double %a, double* %a.addr, align 8
  store i32 %b, i32* %b.addr, align 4
  %0 = load double, double* %a.addr, align 8
  %1 = load i32, i32* %b.addr, align 4
  %conv = sitofp i32 %1 to double
  %add = fadd double %0, %conv
  %conv1 = fptrunc double %add to float
  ret float %conv1
}

; Function Attrs: nounwind uwtable
define double @dbl_sum(double %a, double %b) #0 {
entry:
  %a.addr = alloca double, align 8
  %b.addr = alloca double, align 8
  store double %a, double* %a.addr, align 8
  store double %b, double* %b.addr, align 8
  %0 = load double, double* %a.addr, align 8
  %1 = load double, double* %b.addr, align 8
  %add = fadd double %0, %1
  ret double %add
}

; Function Attrs: nounwind uwtable
define i32 @sum_int_int(i32 %a, i32 %b) #0 {
entry:
  %a.addr = alloca i32, align 4
  %b.addr = alloca i32, align 4
  store i32 %a, i32* %a.addr, align 4
  store i32 %b, i32* %b.addr, align 4
  %0 = load i32, i32* %a.addr, align 4
  %1 = load i32, i32* %b.addr, align 4
  %add = add nsw i32 %0, %1
  ret i32 %add
}

; Function Attrs: nounwind uwtable
define i32 @main(i32 %argc, i8** %argv) #0 {
entry:
  %retval = alloca i32, align 4
  %argc.addr = alloca i32, align 4
  %argv.addr = alloca i8**, align 8
  %x = alloca i32, align 4
  %y = alloca i32, align 4
  %z = alloca float, align 4
  %k = alloca double, align 8
  store i32 0, i32* %retval, align 4
  store i32 %argc, i32* %argc.addr, align 4
  store i8** %argv, i8*** %argv.addr, align 8
  store i32 2, i32* %x, align 4
  store i32 5, i32* %y, align 4
  store float 0x40059999A0000000, float* %z, align 4
  store double 0x408D07D188F42FE8, double* %k, align 8
  %0 = load i32, i32* %x, align 4
  %1 = load i32, i32* %y, align 4
  %call = call i32 @sum_int_int(i32 %0, i32 %1)
  %call1 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str, i32 0, i32 0), i32 %call)
  %2 = load float, float* %z, align 4
  %conv = fpext float %2 to double
  %3 = load i32, i32* %y, align 4
  %call2 = call float @sum_fl_int(double %conv, i32 %3)
  %conv3 = fpext float %call2 to double
  %call4 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str.1, i32 0, i32 0), double %conv3)
  %4 = load double, double* %k, align 8
  %5 = load i32, i32* %x, align 4
  %conv5 = sitofp i32 %5 to double
  %call6 = call double @dbl_sum(double %4, double %conv5)
  %call7 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([5 x i8], [5 x i8]* @.str.2, i32 0, i32 0), double %call6)
  ret i32 0
}

declare i32 @printf(i8*, ...) #1

attributes #0 = { nounwind uwtable "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.ident = !{!0}

!0 = !{!"clang version 3.8.0 (tags/RELEASE_380/final)"}
""")

    assert result[0] == "%d\n"
    assert result[1] == "7"
    assert result[2] == "%f\n"
    assert result[3][:3] == "7.7"
    assert result[4] == "%lf\n"
    assert result[5] == "930.977312"
