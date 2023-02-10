'''
The Command-Line/Terminal interface for BCL.
'''
# TODO: REMOVE OR FINISH

from dataclasses import dataclass
from typing import Callable, Union

import errors

argTypes = Union[list,bool,str]
argsDict = dict[str, argTypes]


def parse_compile(args: list[str]) -> argsDict:
    import compile

    compile.compile_file(args[1], args[1:])


MODES = {"compile": parse_compile}

valid_args = {
    "--emit-object": False,
    "--emit-binary": False,
    "--dev": False,
    "--libs": []
}


def parse_command(args: list[str]) -> Any:
    if args[0] not in MODES.keys():
        errors.error(f"Invalid Command Line Arguments.\n  No sub-command: {args[0]}")

    MODES[args[0]](args)


def parse_args(args: list[str]) -> argsDict:
    '''creates a dictionary of command-line arguments.'''
    args_dict: argsDict = { # contains all valid command line arguments
            "--emit-object": False,
            "--emit-binary": False,
            "--dev": False
        }
    for arg in args:
        if not arg.startswith('-'):
            continue
        if '=' not in arg:
            args_dict[arg] = not args_dict[arg]  # invert current value
        else:
            name, value = arg.split('=')
            if "," in value:
                args_dict[name] = value.split(",")
            elif isinstance(args_dict[name], list):
                args_dict[name] = [value]
            else:
                args_dict[name] = value
    return args_dict
