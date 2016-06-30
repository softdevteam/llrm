from base_bytecode_test import BaseBytecodeTest

def test_arithmetic():
    interp = BaseBytecodeTest()
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
    interp = BaseBytecodeTest()
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
    interp = BaseBytecodeTest()
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

def test_branching():
    interp = BaseBytecodeTest()
    argc = 1
    argv = ["temp.bc"]
    result = interp.run_bytecode(argc, argv, r"""
; ModuleID = 'test.bc'
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str = private unnamed_addr constant [4 x i8] c"%d\0A\00", align 1

; Function Attrs: nounwind uwtable
define i32 @sum(i32 %n) #0 {
entry:
  %retval = alloca i32, align 4
  %n.addr = alloca i32, align 4
  store i32 %n, i32* %n.addr, align 4
  %0 = load i32, i32* %n.addr, align 4
  %cmp = icmp sgt i32 %0, 0
  br i1 %cmp, label %if.then, label %if.end

if.then:                                          ; preds = %entry
  %1 = load i32, i32* %n.addr, align 4
  %2 = load i32, i32* %n.addr, align 4
  %sub = sub nsw i32 %2, 1
  %call = call i32 @sum(i32 %sub)
  %add = add nsw i32 %1, %call
  store i32 %add, i32* %retval, align 4
  br label %return

if.end:                                           ; preds = %entry
  store i32 0, i32* %retval, align 4
  br label %return

return:                                           ; preds = %if.end, %if.then
  %3 = load i32, i32* %retval, align 4
  ret i32 %3
}

; Function Attrs: nounwind uwtable
define i32 @main(i32 %argc, i8** %argv) #0 {
entry:
  %retval = alloca i32, align 4
  %argc.addr = alloca i32, align 4
  %argv.addr = alloca i8**, align 8
  %i = alloca i32, align 4
  store i32 0, i32* %retval, align 4
  store i32 %argc, i32* %argc.addr, align 4
  store i8** %argv, i8*** %argv.addr, align 8
  %call = call i32 @sum(i32 10)
  %call1 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str, i32 0, i32 0), i32 %call)
  %0 = load i32, i32* %argc.addr, align 4
  %mul = mul nsw i32 3, %0
  store i32 %mul, i32* %i, align 4
  br label %while.cond

while.cond:                                       ; preds = %while.body, %entry
  %1 = load i32, i32* %i, align 4
  %dec = add nsw i32 %1, -1
  store i32 %dec, i32* %i, align 4
  %cmp = icmp sgt i32 %1, 0
  br i1 %cmp, label %while.body, label %while.end

while.body:                                       ; preds = %while.cond
  %2 = load i32, i32* %i, align 4
  %call2 = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str, i32 0, i32 0), i32 %2)
  br label %while.cond

while.end:                                        ; preds = %while.cond
  ret i32 0
}

declare i32 @printf(i8*, ...) #1

attributes #0 = { nounwind uwtable "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.ident = !{!0}

!0 = !{!"clang version 3.8.0 (tags/RELEASE_380/final)"}
""")

    assert result[0] == "%d\n"
    assert result[1] == "55"
    assert result[3] == "2"
    assert result[5] == "1"
    assert result[7] == "0"

def test_phi00():
    interp = BaseBytecodeTest()
    argc = 2
    argv = ["temp.bc", "2"]
    result = interp.run_bytecode(argc, argv, r"""
; ModuleID = 'test.bc'
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"
@.str = private unnamed_addr constant [4 x i8] c"%d\0A\00", align 1
; Function Attrs: nounwind uwtable
define i32 @main(i32 %argc, i8** nocapture readnone %argv) #0 {
entry:
  br label %for.body
for.cond.cleanup:                                 ; preds = %if.end5
  ret i32 0
for.body:                                         ; preds = %if.end5, %entry
  %i.016 = phi i32 [ 1, %entry ], [ %inc6, %if.end5 ]
  %x.015 = phi i32 [ 8, %entry ], [ %x.1, %if.end5 ]
  %argc.addr.014 = phi i32 [ %argc, %entry ], [ %argc.addr.1, %if.end5 ]
  %rem = srem i32 %argc.addr.014, 5
  %cmp1 = icmp eq i32 %rem, 0
  br i1 %cmp1, label %if.then, label %if.else
if.then:                                          ; preds = %for.body
  %inc = add nsw i32 %x.015, 1
  br label %if.end5
if.else:                                          ; preds = %for.body
  %cmp2 = icmp slt i32 %i.016, 5
  %cmp3 = icmp sgt i32 %argc.addr.014, 1
  %or.cond = and i1 %cmp3, %cmp2
  %add = add nsw i32 %argc.addr.014, 2
  %add.argc.addr.0 = select i1 %or.cond, i32 %add, i32 %argc.addr.014
  %.x.0 = select i1 %or.cond, i32 10, i32 %x.015
  br label %if.end5
if.end5:                                          ; preds = %if.else, %if.then
  %argc.addr.1 = phi i32 [ %argc.addr.014, %if.then ], [ %add.argc.addr.0, %if.else ]
  %x.1 = phi i32 [ %inc, %if.then ], [ %.x.0, %if.else ]
  %call = tail call i32 (i8*, ...) @printf(i8* nonnull getelementptr inbounds ([4 x i8], [4 x i8]* @.str, i64 0, i64 0), i32 %x.1)
  %inc6 = add nuw nsw i32 %i.016, 1
  %exitcond = icmp eq i32 %inc6, 11
  br i1 %exitcond, label %for.cond.cleanup, label %for.body
}
; Function Attrs: nounwind
declare i32 @printf(i8* nocapture readonly, ...) #1
attributes #0 = { nounwind uwtable "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { nounwind "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }
!llvm.ident = !{!0}
!0 = !{!"clang version 3.8.0 (tags/RELEASE_380/final)"}
""")

    assert result[0] == "%d\n"
    assert result[1] == "10"
    assert result[3] == "10"
    assert result[5] == "10"
    assert result[7] == "10"
    assert result[9] == "11"
    assert result[11] == "12"
    assert result[13] == "13"
    assert result[15] == "14"
    assert result[17] == "15"
    assert result[19] == "16"

def test_phi01():
    interp = BaseBytecodeTest()
    argc = 1
    argv = ["temp.bc"]
    result = interp.run_bytecode(argc, argv, r"""
; ModuleID = 'test.bc'
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str = private unnamed_addr constant [4 x i8] c"%d\0A\00", align 1

; Function Attrs: nounwind uwtable
define i32 @main(i32 %argc, i8** nocapture readnone %argv) #0 {
entry:
  br label %for.body

for.cond.cleanup:                                 ; preds = %if.end12
  ret i32 0

for.body:                                         ; preds = %if.end12, %entry
  %i.023 = phi i32 [ 0, %entry ], [ %inc13, %if.end12 ]
  %x.022 = phi i32 [ 8, %entry ], [ %x.1, %if.end12 ]
  %rem = srem i32 %i.023, 4
  switch i32 %rem, label %if.else9 [
    i32 0, label %if.end12
    i32 1, label %if.then4
    i32 2, label %if.then8
  ]

if.then4:                                         ; preds = %for.body
  %add = add nsw i32 %x.022, 2
  br label %if.end12

if.then8:                                         ; preds = %for.body
  %inc = add nsw i32 %x.022, 1
  br label %if.end12

if.else9:                                         ; preds = %for.body
  %add10 = add nsw i32 %x.022, 3
  br label %if.end12

if.end12:                                         ; preds = %for.body, %if.then4, %if.else9, %if.then8
  %x.1 = phi i32 [ %add, %if.then4 ], [ %inc, %if.then8 ], [ %add10, %if.else9 ], [ 10, %for.body ]
  %call = tail call i32 (i8*, ...) @printf(i8* nonnull getelementptr inbounds ([4 x i8], [4 x i8]* @.str, i64 0, i64 0), i32 %x.1)
  %inc13 = add nuw nsw i32 %i.023, 1
  %exitcond = icmp eq i32 %inc13, 13
  br i1 %exitcond, label %for.cond.cleanup, label %for.body
}

; Function Attrs: nounwind
declare i32 @printf(i8* nocapture readonly, ...) #1

attributes #0 = { nounwind uwtable "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { nounwind "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.ident = !{!0}

!0 = !{!"clang version 3.8.0 (tags/RELEASE_380/final)"}
""")
#################################################################

#include <stdio.h>
#
#int main(int argc, char *argv[])
#{
#    int x = 8;
#
#    for(int i = 0; i < 13; ++i) {
#
#        if(i % 4 == 0) {
#            x = 10;
#        }
#        else if(i % 4 == 1) {
#            x += 2;
#        }
#        else if(i % 4 == 2){
#            ++x;
#        }
#        else {
#            x += 3;
#        }
#        printf("%d\n", x);
#    }
#    return 0;
#}

    correct_result = []
    for i in range(0, 13):
        if i % 4 == 0:
            x = 10
        elif i % 4 == 1:
            x += 2
        elif i % 4 == 2:
            x += 1
        else:
            x += 3
        correct_result.extend(["%d\n", str(x)])
    for i in range(len(result)):
        assert result[i] == correct_result[i]

def test_phi02():
    interp = BaseBytecodeTest()
    argc = 1
    argv = ["temp.bc"]
    result = interp.run_bytecode(argc, argv, r"""

@.str = private unnamed_addr constant [7 x i8] c"%d %d\0A\00", align 1

define i32 @main(i32 %argc, i8** %argv) {
entry:
  %x.addr = alloca i32, align 4
  %y.addr = alloca i32, align 4
  store i32 2, i32* %x.addr, align 4
  store i32 5, i32* %y.addr, align 4

  %x = load i32, i32* %x.addr, align 4
  %y = load i32, i32* %y.addr, align 4

  %cmp = icmp eq i32 %argc, 2

  br i1 %cmp, label %if.then, label %if.else

if.then:
  %x0 = add nsw i32 %x, 1
  br label %if.end

if.else:
  %y0 = add nsw i32 %y, 1
  br label %if.end

if.end:
  %x1 = phi i32 [ %x0, %if.then ], [ %x, %if.else ]
  %y1 = phi i32 [ %y, %if.then ], [ %y0, %if.else ]
  %call = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([7 x i8], [7 x i8]* @.str, i64 0, i64 0), i32 %x1, i32 %y1)
  ret i32 0
}

declare i32 @printf(i8*, ...)

""")
    assert result[0] == "%d %d\n"
    assert result[1] == "2"
    assert result[2] == "6"
