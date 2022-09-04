RED = "\u001b[31m"
RESET = "\u001b[0m"
YELLOW = "\u001b[33;1m"
GREEN = "\u001b[32m"
ORANGE = "\u001b[38;5;209;1m"
PURPLE = "\u001b[35m"


SILENT_MODE = False
PROFILING = False

def _print_text(text):
    '''print text with preceeding '|' regardless of line count'''
    if SILENT_MODE: return None

    [print(f'| {x}') for x in text.split('\n')]


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

def output_profile_info(name: str, mem_bytes: int):
    if SILENT_MODE or not PROFILING: return None

    print(PURPLE, end='')
    print(f"| PROFILER:{name} >> {mem_bytes:+,} bytes")
    print(RESET, end='')

def profile_info(obj, detailed = False):
    if SILENT_MODE or not PROFILING: return None

    obj._mem_profile(detailed = detailed)