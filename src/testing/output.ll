; ModuleID = "/media/taustin/1TB hardrive/Users/Whirl/Documents/programs and projects/2021/compiledProgrammingLanguage/src/codegen.py"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = ""

define void @"main"() 
{
entry:
  %".2" = bitcast [5 x i8]* @"fstr_int_n" to i8*
  %".3" = bitcast [5 x i8]* @"fstr_string_n" to i8*
  %".4" = add i32 4, 4
  %".5" = call i32 (i8*, ...) @"printf"(i8* %".2", i32 %".4")
  %".6" = sub i32 2, 9
  %".7" = call i32 (i8*, ...) @"printf"(i8* %".2", i32 %".6")
  %".8" = call i32 (i8*, ...) @"printf"(i8* %".2", i32 2)
  %".9" = bitcast [7 x i8]* @"StringConst_0" to i8*
  %".10" = call i32 (i8*, ...) @"printf"(i8* %".3", i8* %".9")
  ret void
}

declare i32 @"printf"(i8* %".1", ...) 

@"fstr_int_n" = internal constant [5 x i8] c"%i \0a\00"
@"fstr_int" = internal constant [4 x i8] c"%i \00"
@"fstr_string_n" = internal constant [5 x i8] c"%s \0a\00"
@"fstr_string" = internal constant [4 x i8] c"%s \00"
@"StringConst_0" = internal constant [7 x i8] c"poggers"