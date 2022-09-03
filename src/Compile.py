

from contextlib import contextmanager
from time import perf_counter

import Errors
from Errors import _print_text, inline_warning

@contextmanager
def timingContext(text: str):
    start = perf_counter()
    yield
    _print_text(f'{text} in {perf_counter() - start} seconds')

def compile(src_str: str, output_loc: str):
    start = perf_counter()

    inline_warning("Python has notoriusly high memory usage, this applies for this compiler!\nThis compiler is written in python with llvmlite!")
    print()

    print(f'{Errors.GREEN}/------------------------------------------------#')

    with timingContext('imports'):
        import Ast.Standard_Functions
        import Codegen
        import Parser_Base
        import Parser
        from Ast import Function
        import Lexer as lex
        from Lexer import Lexer

    with timingContext('lexing finished'):
        tokens = lex.get_tokens(src_str)
    
    with timingContext('parsing finished'):
        codegen = Codegen.CodeGen()
    
        module = codegen.module
        Ast.Standard_Functions.declare_printf(module)

        pg = Parser.parser(tokens, module)
        parsed = pg.parse()
        
    with timingContext('module created'):
        for x in parsed:
            if not x.completed:
                print(x)
                Errors.error(f"""
                The compiler could not complete all it's operations.

                Note: this is an error the compiler was not designed to catch.
                    If you encounter this, send all relavent information to language devs.
                """, line = x.pos)
                

            x.value.pre_eval()

        for x in parsed:
            x.value.eval()
    
    codegen.save_ir(output_loc)

    print(f'| IR saved, compilation done | {perf_counter() - start}s')
    print(f'\\--------------------------------------------------/{Errors.RESET}')
    print()

    import os, psutil
    process = psutil.Process(os.getpid())
    Errors.inline_warning(f'{process.memory_info().rss} bytes of memory used for this operation.')  # in bytes 


    print('\n\n\n')
