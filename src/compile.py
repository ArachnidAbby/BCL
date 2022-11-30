import os
import sys
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter

import errors
from errors import _print_raw, _print_text, inline_warning


@contextmanager
def timingContext(text: str):
    start = perf_counter()
    yield
    _print_text(f'{errors.GREEN}{text} in {perf_counter() - start} seconds')

def compile(src_str: str, output_loc: str):
    start = perf_counter()

    inline_warning("Python has notoriusly high memory usage, this applies for this compiler!\nThis compiler is written in python with llvmlite!")
    _print_raw("")

    _print_raw(f'{errors.GREEN}/------------------------------------------------#')

    with timingContext('imports finished'):
        import psutil

        process = psutil.Process(os.getpid())
        tmp = imports_mem = process.memory_info().rss
        import codegen

        codegen = codegen.CodeGen()
        imports_mem = process.memory_info().rss - tmp
        import parser

        import Ast.standardfunctions
        import lexer as lex

    with timingContext('lexing finished'):
        tokens = lex.get_tokens(src_str)
    
    with timingContext('parsing finished'):
        module = codegen.module
        Ast.standardfunctions.declare_printf(module)
        Ast.standardfunctions.declare_exit(module)
        pg = parser.Parser(tokens, module)
        parsed = pg.parse()
        
    with timingContext('module created'):
        for x in parsed:
            if not x.completed:
                errors.developer_info(f'{x} {parsed}')
                errors.error(f"""
                The compiler could not complete all it's operations.

                Note: this is an error the compiler was not designed to catch.
                    If you encounter this, send all relavent information to language devs.
                """, line = x.pos)
                

            x.value.pre_eval()
        for x in parsed:
            x.value.eval()
    
    codegen.save_ir(output_loc)

    _print_raw(f'| IR saved, compilation done | {perf_counter() - start}s')
    _print_raw(f'\\--------------------------------------------------/{errors.RESET}')
    _print_raw("")

    usage = process.memory_info().rss
    errors.inline_warning(f'{(usage - imports_mem)/1000:,.1f}KB of memory used for this operation.')  # in bytes 


    _print_raw('\n\n\n')

def compile_file(file: Path):
    errors.FILE = file
    with file.open() as f:
        compile(f.read(), str(file.absolute().parents[0] / "output.ll"))
