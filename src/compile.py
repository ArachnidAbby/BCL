import os
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter

import errors
from Ast.nodes.commontypes import SrcPosition
from errors import _print_raw, _print_text, inline_warning

# contains all valid command line arguments
DEFAULT_ARGS: dict[str, bool | str | list] = {
    "--emit-object": False,
    "--emit-binary": False,
    "--dev": False,
    "--emit-ast": False,
    "--supress-warnings": False,
    "--libs": [],
    "--run": False
}


@contextmanager
def timingContext(text: str):
    start = perf_counter()
    yield
    print(errors.GREEN, end="")
    _print_text(f'{text} in {perf_counter() - start} seconds{errors.RESET}')


def compile(src_str: str, output_loc: Path, args, file=""):
    start = perf_counter()

    inline_warning("Python has notoriusly high memory usage, this applies " +
                   "for this compiler!\nThis compiler is written in python " +
                   "with llvmlite!")
    _print_raw("")

    _print_raw(f'{errors.GREEN}/{"-"*48}#{errors.RESET}')
    if args["--supress-warnings"]:
        errors.SUPRESSED_WARNINGS = True

    with timingContext('imports finished'):
        import psutil  # type: ignore

        process = psutil.Process(os.getpid())
        tmp = imports_mem = process.memory_info().rss
        import Ast.module
        import codegen

        codegen.initialize_llvm()
        imports_mem = process.memory_info().rss - tmp

        from rply.errors import LexingError  # type: ignore

        import Ast.functions.standardfunctions
        import lexer as lex
        from Ast import Ast_Types

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
        Ast_Types.definedtypes.types_dict['strlit'] = Ast_Types.definedtypes.types_dict['strlit'](module)
        module.fullfill_templates()
        module.do_scheduled()
        module.post_parse(None)
        module.pre_eval(None)
        module.eval(None)

    # loc = output_loc.parents[0]
    module.save_ir(os.getcwd(), args=args)
    codegen.shutdown_llvm()

    _print_raw(f'{errors.GREEN}| IR saved, compilation done | ' +
               f'{perf_counter() - start}s')
    _print_raw(f'\\{"-"*50}/{errors.RESET}')
    _print_raw("")

    usage = process.memory_info().rss
    errors.inline_warning(f'{(usage - imports_mem)/1000:,.1f}' +
                          'KB of memory used for this operation.')

    _print_raw('\n\n\n')
    if args["--run"] and args["--emit-binary"]:
        os.system(f"{os.getcwd()}/target/output")


def create_args_dict(args: list[str]) -> dict[str, bool | str | list]:
    '''creates a dictionary of command-line arguments.'''
    args_dict: dict[str, bool | str | list] = DEFAULT_ARGS
    for arg in args:
        if not arg.startswith('-'):
            continue
        if arg.split('=')[0] not in args_dict.keys():
            errors.error(f"No command line argument: \"{arg}\"")
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


def compile_file(args):
    file = None
    for arg in args:
        if arg.startswith('--') or arg == "compile":
            continue
        file = Path(arg)
        break

    if file is None:
        errors.error("No file was specified")

    if not os.path.exists(file):
        errors.error(f"No Such file \"{file}\"")


    with file.open() as f:
        args = create_args_dict(args)
        compile(f.read(), file.absolute(), args,
                file=str(file))
