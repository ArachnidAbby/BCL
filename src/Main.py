import os
import sys
from typing import List


def make_project(args: List[str]):
    '''setup project files'''
    if not os.path.isdir(args[1]): os.mkdir(args[1])
    os.mkdir(f"{args[1]}/src")
    os.mkdir(f"{args[1]}/lib")
    with open(f"{args[1]}/project.toml",'w+') as f:
        f.write(f'''[info]
name = "{args[1].split("/")[-1]}"
author = "{os.getlogin()}"
version = "1.0"

[compile]

GC = true
include = [] # include paths, ex: {args[1].split("/")[-1]}/resources/
''')
    with open(f"{args[1]}/src/Main.bcl",'w+') as f:
        f.write('''define main() {
    println("Hello World!");
}
''')
    with open(f"{args[1]}/.gitignore",'w+') as f:
        f.write('''# BCL ignored files
lib/

# other files
''')


def compile(source_code: str, output_loc: str):
    '''compile source code'''
    import time
    start = time.perf_counter()
    start_beginning = start

    import Ast.Standard_Functions
    import Codegen
    import Errors
    import Parser
    from Ast import Function
    from Lexer import Lexer

    Errors.inline_warning("Python has notoriusly high memory usage, this applies in this compiler!\nThis compiler is written in python with llvmlite!")
    print()

    print(f'{Errors.GREEN}/------------------------------------------------#')
    print(f'| imports finished in {time.perf_counter() - start} seconds')

    start=time.perf_counter()

    lexer = Lexer().get_lexer()
    tokens = lexer.lex(example)
    codegen = Codegen.CodeGen()

    module = codegen.module
    Ast.Standard_Functions.declare_printf(module)

    output = []
    for x in tokens:
        output.append({"name":x.name,"value":x.value,"source_pos":[x.source_pos.lineno, x.source_pos.colno, len(x.value)], "completed": False})
    
    print(f'| lexing finished in {time.perf_counter() - start} seconds')

    start=time.perf_counter()

    pg = Parser.parser(output, module)
    parsed = pg.parse()

    print(f'| parsing finished in {time.perf_counter() - start} seconds')

    start=time.perf_counter()
    

    for x in parsed:
        if not x["completed"]:
            Errors.error(f"""
            The compiler could not complete all it's operations.

            Note: this is an error the compiler was not designed to catch.
                  If you encounter this, send all relavent information to language devs.
            """, line = x['source_pos'])

        x["value"].pre_eval()

    for x in parsed:
        x["value"].eval()
    
    
    print(f'| module created in {time.perf_counter() - start} seconds')

    start=time.perf_counter()

    
    codegen.save_ir(output_loc)

    print(f'| IR saved, compilation done | {time.perf_counter() - start_beginning}s')
    print(f'\\--------------------------------------------------/{Errors.RESET}')
    print()
    import os, psutil
    process = psutil.Process(os.getpid())
    Errors.inline_warning(f'{process.memory_info().rss} bytes of memory used for this operation.')  # in bytes 


    print('\n\n\n')
    # print(module, type(module))


if __name__ == "__main__":
    args = sys.argv
    if args[0]=="src/Main.py": args=args[1::]

    if len(args)==0:
        print("Valid sub-commands: build, run, make, publish")

    elif args[0] == "make": 
        make_project(args)

    else:
        example = '''

define main() {
    x = 69+1;
    //j = x+4-2*6/7%12;
    9 and 2;
    if not x>=2000 and x <= 70 {
        println(x*1);
    }else if x<=2{
        println(x*5);
    } else {
        println(98549885984);
    }

    println(82);
    //fizzbuzz(0);
}

define test() {
    9;
}

//define as_int(in: bool) -> i32 {
//    //really bad as_int function as a proof of concept.
//    //its bad because the compiler will still try the multiplication.
//    // which is just an extra instruction.
//    return in*1;
//}

//define remainder_test(value: i32, divider: i32) -> bool {
//    // random test function with new return statements.
//    return (value % divider) == 0;
//}

//define fizzbuzz(current: i32) {
//    // prints 1 for "fizz"
//    // prints 2 for "buzz"
//    // prints 3 for "fizzbuzz"
//    fizz = remainder_test(current, 3).as_int();
//    buzz = remainder_test(current, 5)*2;
//
//    println(fizz+buzz); 
//
//    fizzbuzz(current+1);
//}

'''
        compile(example, "test.ll")
