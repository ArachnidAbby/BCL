from contextlib import contextmanager
from pathlib import Path
from time import perf_counter

import Errors
from Errors import _print_text, inline_warning

@contextmanager
def timingContext(text: str):
    start = perf_counter()
    yield
    _print_text(f'{Errors.GREEN}{text} in {perf_counter() - start} seconds')

def compile(src_str: str, output_loc: str):
    start = perf_counter()

    inline_warning("Python has notoriusly high memory usage, this applies for this compiler!\nThis compiler is written in python with llvmlite!")
    print()

    print(f'{Errors.GREEN}/------------------------------------------------#')

    with timingContext('imports finished'):
        import os, psutil, sys
        process = psutil.Process(os.getpid())
        tmp = imports_mem = process.memory_info().rss
        import Codegen
        codegen = Codegen.CodeGen()
        imports_mem = process.memory_info().rss - tmp
        import Ast.Standard_Functions
        import Parser
        import Lexer as lex

    with timingContext('lexing finished'):
        tokens = lex.get_tokens(src_str)
    
    with timingContext('parsing finished'):
        
    
        module = codegen.module
        Ast.Standard_Functions.declare_printf(module)

        pg = Parser.parser(tokens, module)
        parsed = pg.parse()
        Errors.output_mem_prof("ParserClassObject", sys.getsizeof(parsed))
        
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
        Errors.output_mem_prof("ParserClassObject--2", sys.getsizeof(parsed))
    
    codegen.save_ir(output_loc)

    print(f'| IR saved, compilation done | {perf_counter() - start}s')
    print(f'\\--------------------------------------------------/{Errors.RESET}')
    print()

    usage = process.memory_info().rss
    Errors.inline_warning(f'{(usage - imports_mem)/1000:,.1f}KB of memory used for this operation.')  # in bytes 


    print('\n\n\n')


def compile_silent(src_str: str, output_loc: str):
    import Ast.Standard_Functions
    import Codegen
    import Parser
    import Lexer as lex

    tokens = lex.get_tokens(src_str)
    
    codegen = Codegen.CodeGen()
    
    module = codegen.module
    Ast.Standard_Functions.declare_printf(module)

    pg = Parser.parser(tokens, module)
    parsed = pg.parse()
        
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

def compile_file(file: Path):
    with file.open() as f:
        compile(f.read(), str(file.absolute().parents[0] / "output.ll"))