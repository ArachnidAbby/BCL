import os
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter

import errors
from Ast.nodes.commontypes import SrcPosition
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


def compile(src_str: str, output_loc: Path, args, file=""):
    start = perf_counter()

    inline_warning("Python has notoriusly high memory usage, this applies for this compiler!\nThis compiler is written in python with llvmlite!")
    _print_raw("")

    _print_raw(f'{errors.GREEN}/------------------------------------------------#{errors.RESET}')

    with timingContext('imports finished'):
        import psutil

        process = psutil.Process(os.getpid())
        tmp = imports_mem = process.memory_info().rss
        import Ast.module
        import codegen

        code_gen = codegen.CodeGen()
        imports_mem = process.memory_info().rss - tmp

        from rply.errors import LexingError

        import Ast.functions.standardfunctions
        import lexer as lex

    with timingContext('lexing finished'):
        tokens = lex.Lexer().get_lexer().lex(src_str)

    with timingContext('parsing finished'):
        try:
            module = Ast.module.Module(SrcPosition.invalid(), output_loc.stem,
                                       str(file), tokens)
            module.parse()
        except LexingError as e:
            error_pos = e.source_pos
            pos = SrcPosition(error_pos.lineno, error_pos.colno, 0, str(file))
            errors.error("A Lexing Error has occured. Invalid Syntax",
                         line=pos, full_line=True)

    with timingContext('module created'):
        module.pre_eval()
        module.eval()

    module.save_ir(output_loc.parents[0], args=args)
    code_gen.shutdown()

    _print_raw(f'{errors.GREEN}| IR saved, compilation done | {perf_counter() - start}s')
    _print_raw(f'\\--------------------------------------------------/{errors.RESET}')
    _print_raw("")

    usage = process.memory_info().rss
    errors.inline_warning(f'{(usage - imports_mem)/1000:,.1f}KB of memory used for this operation.')  # in bytes

    _print_raw('\n\n\n')


def create_args_dict(args: list[str]) -> dict[str, bool | str | list]:
    '''creates a dictionary of command-line arguments.'''
    args_dict: dict[str, bool | str | list] = DEFAULT_ARGS
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
    if not os.path.exists(file):
        errors.error(f"No Such file \"{file}\"")

    with file.open() as f:
        args = create_args_dict(args)
        compile(f.read(), file.absolute(), args,
                file=str(file))
