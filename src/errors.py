'''This module is used to print errors, warning etc. It does all the proper formatting.'''

import sys
from inspect import currentframe, getframeinfo
from typing import Sequence

RED = "\u001b[31m"
RESET = "\u001b[0m"
YELLOW = "\u001b[33;1m"
GREEN = "\u001b[32m"
ORANGE = "\u001b[38;5;209;1m"
PURPLE = "\u001b[35m"
MAGENTA = "\u001b[35m"
CODE125 = "\u001b[38;5;125m"
CODE202 = "\u001b[38;5;202m"
CODE177 = "\u001b[38;5;177m"

SILENT_MODE = False
PROFILING = False
FILE = ""

USES_FEATURE: dict[str, bool] = {} #give warning about used features

def _print_text(text):
    '''print text with preceeding '|' regardless of line count'''
    if SILENT_MODE:
        return

    for line in text.split('\n'):
        print(f'| {line}')

def _print_raw(text):
    '''print text unless SILENT_MODE is active'''
    if SILENT_MODE:
        return

    print(text)


def error(text: str, line = (-1,-1,-1), full_line=False):
    '''prints an error with a line # if provided'''
    if SILENT_MODE:
        sys.exit(1)

    code_line = show_error_spot(FILE, line, full_line)

    largest = max(
        [len(x) for x in f"| {text}".split('\n')]+
        [len(f"|    Line: {line[0]}")]+
        [len(code_line.split('\n')[0])]
    )
    print(f'{RED}#{"-"*(largest//4)}')

    _print_text(text)
    if line!= (-1,-1,-1):
        print(f'|    Line: {line[0]}')
        print("#"+"-"*len(code_line.split('\n')[0]))
        print(f"{RESET}{code_line}")
    print(f'{RED}\\{"-"*(largest-1)}/{RESET}')
    print("\n\n\n\n")
    sys.exit(1)

def inline_warning(text: str, line = (-1,-1,-1)):
    '''displays a warning without any special formatting encasing it.'''
    if SILENT_MODE:
        return

    print(ORANGE, end='')
    _print_text(text)
    if line!= (-1,-1,-1):
        print(f'|    Line: {line[0]}')
    print(RESET, end='')

def developer_warning(text: str):
    '''give warnings to developers of the language that unsupported behavior is being used.'''
    if SILENT_MODE:
        return

    print(CODE125, end='')

    if (frame:=currentframe()) is not None:
        frameinfo = getframeinfo(frame)
        _print_text(f"{text}\n\t at: {frameinfo.filename}, {frameinfo.lineno}")

    print(RESET, end='')

def developer_info(text):
    '''print info directed at the developer. This is profiling infomation used \
    for debugging purposes'''
    if SILENT_MODE or not PROFILING:
        return

    print(CODE125, end='')
    print(f"| {text}")
    print(RESET, end='')

def experimental_warning(text: str, possible_bugs: Sequence[str]):
    '''gives a warning about the use of experimental features and risks involved.'''
    if SILENT_MODE:
        return
    line_size = 35
    print(CODE202, end='')
    print(f'#{"-"*(line_size)}')
    bugs = '\n'.join(('\t- '+bug for bug in possible_bugs))
    _print_text(f"EXPERIMENTAL FEATURE WARNING::\n  {text}\n\n  POSSIBLE BUGS INCLUDE:\n{bugs}")
    print(f'#{"-"*(line_size)}')
    print(RESET, end='')

def show_error_spot(file_loc, position: tuple[int, int, int], use_full_line: bool) -> str:
    if position == (-1,-1,-1):
        return ""
    full_line = ""
    with open(file_loc, 'r') as fp:
        for i, line in enumerate(fp):
            if i == position[0]-1:
                full_line = line.strip('\n')
                break
    if use_full_line:
        underline = "^"*len(full_line)
    else:
        underline = " "*(position[1]-1) + "^"*position[2]
    full_line_len = len(full_line)
    full_line = full_line.strip()
    underline = underline[full_line_len-len(full_line):]
    
    return f"{RED}|    {RESET}{full_line}\n{RED}|    {CODE177}{underline}{RESET}"

