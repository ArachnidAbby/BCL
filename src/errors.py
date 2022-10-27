from inspect import currentframe, getframeinfo

RED = "\u001b[31m"
RESET = "\u001b[0m"
YELLOW = "\u001b[33;1m"
GREEN = "\u001b[32m"
ORANGE = "\u001b[38;5;209;1m"
PURPLE = "\u001b[35m"
MAGENTA = "\u001b[35m"
CODE125 = u"\u001b[38;5;125m" 


SILENT_MODE = False
PROFILING = False

def _print_text(text):
    '''print text with preceeding '|' regardless of line count'''
    if SILENT_MODE: return None

    for x in text.split('\n'): print(f'| {x}')


def error(text: str, line = (-1,-1,-1)):
    if SILENT_MODE: quit()

    largest = max(
        [len(x) for x in f"| {text}".split('\n')]+
        [len(f"|    Line: {line[0]}")]
    )
    print(f'{RED}#{"-"*(largest//4)}')
    # print(f'| {text}')
    _print_text(text)
    if line!= (-1,-1,-1): print(f'|    Line: {line[0]}')
    print(f'\\{"-"*(largest-1)}/{RESET}')
    print("\n\n\n\n")
    quit()

def inline_warning(text: str, line = (-1,-1,-1)):
    if SILENT_MODE: return None

    print(ORANGE, end='')
    _print_text(text)
    if line!= (-1,-1,-1): print(f'|    Line: {line[0]}')
    print(RESET, end='')

def developer_warning(text: str):
    '''give warnings to developers of the language that unsupported behavior is being used.'''
    if SILENT_MODE: return None

    print(CODE125, end='')

    frameinfo = getframeinfo(currentframe())
    _print_text(text + f"\n\t at: {frameinfo.filename}, {frameinfo.lineno}")
    
    print(RESET, end='')

def output_profile_info(text):
    if SILENT_MODE or not PROFILING: return None

    print(PURPLE, end='')
    print(f"| {text}")
    print(RESET, end='')

def output_mem_prof(name: str, mem_bytes: int):
    if SILENT_MODE or not PROFILING: return None

    print(PURPLE, end='')
    print(f"| PROFILER:{name} >> {mem_bytes:+,} bytes")
    print(RESET, end='')

def profile_info(obj, detailed = False):
    if SILENT_MODE or not PROFILING: return None

    obj._mem_profile(detailed = detailed)