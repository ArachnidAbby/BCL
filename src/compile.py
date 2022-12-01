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
    print(errors.GREEN, end="")
    _print_text(f'{text} in {perf_counter() - start} seconds')

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
        for c, x in enumerate(parsed):
            if not x.completed:
                if x.name in ["OPEN_CURLY_USED", "OPEN_PAREN_USED"] and parsed[c+1].completed:
                    continue
                    
                if x.name == "CLOSED_SQUARE" and parsed[c+1].completed:
                    errors.error(f"""
                    Unclosed square brackets
                    """.strip(), line = x.pos)

                errors.developer_info(f'item: {x}   in: {parsed}')

                reached_semicolon = False
                last_pos = (-1,-1,-1)
                for err in parsed[c:]:
                    if err.completed: break
                    if err.name == "SEMI_COLON":
                        reached_semicolon = True
                    last_pos = x.pos
                
                if not reached_semicolon:
                    errors.error(f"""
                    Missing semicolon
                    """.strip(), line = last_pos, full_line= True)
                
                errors.error(f"""
                Syntax error or compiler bug. If you have questions, ask on the github issues page.
                (or use '--dev' when compiling to see the remaining tokens)
                """.strip(), line = x.pos, full_line = True)
                

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
