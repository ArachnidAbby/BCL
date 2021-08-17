; ModuleID = "/media/taustin/1TB hardrive/Users/Whirl/Documents/programs and projects/2021/compiledProgrammingLanguage/src/codegen.py"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = ""

define void @"main"() 
{
entry:
  %".2" = add i32 4, 4
  %".3" = bitcast [5 x i8]* @"fstr_int_n" to i8*
  %".4" = call i32 (i8*, ...) @"printf"(i8* %".3", i32 %".2")
  %".5" = sub i32 2, 9
  %".6" = bitcast [5 x i8]* @"fstr_int_n" to i8*
  %".7" = call i32 (i8*, ...) @"printf"(i8* %".6", i32 %".5")
  %".8" = sub i32 2, 2
  %".9" = bitcast [5 x i8]* @"fstr_int_n" to i8*
  %".10" = call i32 (i8*, ...) @"printf"(i8* %".9", i32 %".8")
  ret void
}

declare i32 @"printf"(i8* %".1", ...) 

@"fstr_int_n" = internal constant [5 x i8] c"%i \0a\00"
@"fstr_int" = internal constant [4 x i8] c"%i \00"