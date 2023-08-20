import os
import shutil
import sys
from pathlib import Path
from typing import List

import compile
import errors
import platform

PATH = os.path.dirname(os.path.realpath(__file__))

if platform.system() == "Windows":
    os.system("")

HELP = """Commands:

compile <src> [..args]
    compile a file
    args:
        --supress-warnings
        --emit-binary (auto enables --emit-object)
        --emit-object (.o files emited)
        --emit-ast (returns the AST, WARNING: VERY LONG OUTPUT)
        --libs=[libs seperated by commas] \
(some libs might need to be prefixed with ':')
        --run execute after compilation
        --dev (additional information used during development of the language)
help
    you are already here?

make <name>
    Makes a project, unfinished

"""


def make_project(args: List[str]):
    '''setup project files'''
    template = "helloworld"

    if not os.path.isdir(args[2]):
        os.mkdir(args[2])

    if len(args) == 4:
        template = args[3]

    os.mkdir(f"{args[2]}/src")
    os.mkdir(f"{args[2]}/lib")

    shutil.copyfile(f"{PATH}/templates/{template}/project.toml", f"{args[2]}/project.toml")
    with open(f"{args[2]}/project.toml",'r+', encoding='UTF-8') as f:
        contents = f.read()
        f.seek(0, 0)
        f.write(contents.format(AUTHOR=os.getlogin(), PROJECT_NAME=args[2]))
    shutil.copyfile(f"{PATH}/templates/{template}/src/main.bcl", f"{args[2]}/src/main.bcl")
    shutil.copyfile(f"{PATH}/templates/{template}/.gitignore", f"{args[2]}/.gitignore")


def main():
    args = sys.argv

    if "--dev" in args:
        errors.PROFILING = True

    if len(args) == 1:
        errors.error("Valid sub-commands: compile, make, publish (Only compile works)")

    elif args[1] == "make":
        make_project(args)

    elif args[1] == "compile":
        compile.compile_file(args[1:])

    elif args[1] == "help":
        length = max([len(x) for x in HELP.split('\n')]) + 2
        print(f"{errors.GREEN}")
        print(f"/{'-'*length}#")
        errors._print_text(HELP)
        print(f"\\{'-'*length}/")
        print(errors.RESET)

    else:
        print(f"Invalid sub-command: {args[1]}")


if __name__ == "__main__":
    main()
