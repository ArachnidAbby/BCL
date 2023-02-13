import os
import shutil
import sys
from pathlib import Path
from typing import List

import compile
import errors

PATH = os.path.dirname(os.path.realpath(__file__))


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

if __name__ == "__main__":
    args = sys.argv

    if "--dev" in args:
        errors.PROFILING = True

    if len(args)==1:
        errors.error("Valid sub-commands: compile, run, make, publish (Only compile works)")

    elif args[1] == "make":
        make_project(args)

    elif args[1] == "compile":
        compile.compile_file(Path(args[2]), args)

    else:
        print(f"Invalid sub-command: {args[1]}")
