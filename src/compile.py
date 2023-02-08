import os
import sys
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import Union

import errors
from errors import _print_raw, _print_text, inline_warning

DEFAULT_ARGS: dict[str, bool|str|list] = {  # contains all valid command line arguments
    "--emit-object": False,
    "--emit-binary": False,
    "--dev": False,
    "--libs": []
}


@contextmanager
def timingContext(text: str):
    start = perf_counter()
    yield
    print(errors.GREEN, end="")
    _print_text(f'{text} in {perf_counter() - start} seconds{errors.RESET}')


def compile(src_str: str, output_loc: str, args):
    start = perf_counter()

    inline_warning("Python has notoriusly high memory usage, this applies for this compiler!\nThis compiler is written in python with llvmlite!")
    _print_raw("")

    _print_raw(f'{errors.GREEN}/------------------------------------------------#{errors.RESET}')

    with timingContext('imports finished'):
        import psutil

        process = psutil.Process(os.getpid())
        tmp = imports_mem = process.memory_info().rss
        import codegen

        code_gen = codegen.CodeGen()
        imports_mem = process.memory_info().rss - tmp

        import Ast.functions.standardfunctions
        import Ast.module
        import lexer as lex

    with timingContext('lexing finished'):
        tokens = lex.Lexer().get_lexer().lex(src_str)

    with timingContext('parsing finished'):
        module = Ast.module.Module((-1, -1, -1), "main", src_str, tokens)
        Ast.functions.standardfunctions.declare_all(module.module)
        module.parse()

    with timingContext('module created'):
        module.pre_eval()
        module.eval()

    module.save_ir(output_loc, args = args)
    code_gen.shutdown()

    _print_raw(f'{errors.GREEN}| IR saved, compilation done | {perf_counter() - start}s')
    _print_raw(f'\\--------------------------------------------------/{errors.RESET}')
    _print_raw("")

    usage = process.memory_info().rss
    errors.inline_warning(f'{(usage - imports_mem)/1000:,.1f}KB of memory used for this operation.')  # in bytes

    _print_raw('\n\n\n')


def create_args_dict(args: list[str]) -> dict[str, bool|str|list]:
    '''creates a dictionary of command-line arguments.'''
    args_dict: dict[str, bool|str|list] = DEFAULT_ARGS
    for arg in args:
        if not arg.startswith('-'):
            continue
        if '=' not in arg:
            args_dict[arg] = not args_dict[arg] # invert current value
        else:
            name, value = arg.split('=')
            if "," in value:
                args_dict[name] = value.split(",")
            elif isinstance(args_dict[name], list):
                args_dict[name] = [value]
            else:
                args_dict[name] = value
    return args_dict


def compile_file(file: Path, args):
    errors.FILE = str(file)

    if not os.path.exists(file):
        errors.error(f"No Such file \"{file}\"")

    with file.open() as f:
        args = create_args_dict(args)
        compile(f.read(), str(file.absolute().parents[0] / "output"), args)
