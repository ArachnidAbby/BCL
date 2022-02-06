; ModuleID = "/run/media/taustin/1TB_hardrive/Users/Whirl/Documents/programs_and_projects/2021/compiledProgrammingLanguage/src/codegen.py"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = ""

define void @"main"() 
{
entry:
  %".2" = bitcast [5 x i8]* @"fstr_int_n" to i8*
  %".3" = bitcast [5 x i8]* @"fstr_string_n" to i8*
  %"test" = alloca i32
  store i32 999, i32* %"test"
  %".5" = load i32, i32* %"test"
  %".6" = call i32 (i8*, ...) @"printf"(i8* %".2", i32 %".5")
  store i32 444, i32* %"test"
  %".8" = load i32, i32* %"test"
  %".9" = call i32 (i8*, ...) @"printf"(i8* %".2", i32 %".8")
  ret void
}

declare i32 @"printf"(i8* %".1", ...) 

@"fstr_int_n" = internal constant [5 x i8] c"%i \0a\00"
@"fstr_int" = internal constant [4 x i8] c"%i \00"
@"fstr_string_n" = internal constant [5 x i8] c"%s \0a\00"
@"fstr_string" = internal constant [4 x i8] c"%s \00"