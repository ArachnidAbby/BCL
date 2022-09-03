import os
import sys
from typing import List

from Parser_Base import ParserBase


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
    import Compile

    Compile.compile(source_code, output_loc)


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
    i = 0;
    loop_amount = 200;

    while i < loop_amount {
        i = i+1;
        fizz = is_multiple(i, 3); 
        buzz = is_multiple(i, 5)*2;
        println(fizz + buzz);
    }
}

define is_multiple(value: i32, divider: i32) -> bool {
    return (value % divider) == 0;
}
'''
        compile(example, "test.ll")
