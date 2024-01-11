'''This module is used to print errors, warning etc.
It does all the proper formatting.'''

import sys
from inspect import currentframe, getframeinfo
from typing import TYPE_CHECKING, NoReturn, Sequence

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexer import RegexLexer
from pygments.token import (Comment, Keyword, Name, Number, Operator,
                            Punctuation, String, Whitespace)

RED = "\u001b[31m"
RESET = "\u001b[0m"
YELLOW = "\u001b[33;1m"
GREEN = "\u001b[32m"
ORANGE = "\u001b[38;5;209;1m"
PURPLE = "\u001b[35m"
MAGENTA = "\u001b[35m"
CODE125 = "\u001b[38;5;125m"
CODE202 = "\u001b[38;5;202m"
CODE214 = "\u001b[38;5;214m"
CODE177 = "\u001b[38;5;177m"

CODE69 = "\u001b[38;5;69m"
CODE81 = "\u001b[38;5;81m"

SILENT_MODE = False
SUPRESSED_WARNINGS = False
PROFILING = False

USES_FEATURE: dict[str, bool] = {}  # give warning about used features


# Silly python hack. My favorite 😋
if TYPE_CHECKING:
    from Ast.nodes.commontypes import SrcPosition
    invalid_pos = SrcPosition.invalid()
else:
    import collections
    SrcPosition = collections.namedtuple('SrcPosition',
                                         ['line', 'col', 'length',
                                          'source_name'])
    invalid_pos = SrcPosition(-1, -1, -1, '')

MultiPosition = SrcPosition | list[SrcPosition]
templating_stack: list[SrcPosition] = []


class BCLLexer(RegexLexer):
    name = 'bcl'
    aliases = ['bcl']
    filenames = ['*.bcl']
    tokens = {
        'root': [
            (r'[\s\n]+', Whitespace),
            (r'(["\'])(?:(?=(\\?))\2.)*?\1', String.Double),
            (r'\d+', Number),
            (r'(if)|(elif)|(else)|(define)|(struct)|(for)|(import)|' +
             r'(yield)|(return)|(for)|(public)|(enum)|(typedef)|(as)',
             Keyword.Reserved),
            (r'(i8)|(i16)|(i32)|(i64)|(u8)|(u16)|(u32)|(u64)|(f64)|' +
             r'(f128)|(bool)|(char)|(strlit)' +
             r'(char)|(str)|(strlit)', Keyword.Type),
            (r'(Self)', Name.Builtin.Pseudo),
            (r'\#\[.*\]', Comment.Preproc),
            (r'\s+((or)|(and)|(not)|(in)|(as))\s+', Operator.Word),
            (r'[\=\+\-\*\\\%\%\<\>\&\^\~\|(\<\<)(\>\>)]', Operator),
            (r'[\{\};\(\)\:\[\]\,(\-\>)\.]', Punctuation),
            (r'[a-zA-Z0-9_]+(?=\(.*\))', Name.Function),
            (r'//.*$', Comment.Single),
            (r'\w[\w\d]*', Name.Other)
        ]
    }


def _print_text(text, color=GREEN):
    '''print text with preceeding '|' regardless of line count'''
    if SILENT_MODE:
        return

    for line in text.split('\n'):
        print(f'{color}| {line}')


def _print_raw(text):
    '''print text unless SILENT_MODE is active'''
    if SILENT_MODE:
        return

    print(text)


def error(text: str, line: MultiPosition = invalid_pos,
          full_line=False, note=None) -> NoReturn:
    '''prints an error with a line # if provided'''
    if SILENT_MODE:
        sys.exit(1)

    file_name = ""
    line_no = -1
    col = -1

    template_additions = ""

    for template in templating_stack:
        temp_col = template[1]
        temp_line = template[0]
        temp_file = template.source_name
        code_line = show_error_spot(template, False)
        template_additions += "| Error constructing templated type:\n" + \
                              f"|    Line: {temp_line}\n" + \
                              f"|    File: {temp_file}:{temp_line}" + \
                              f":{temp_col}" + \
                              f'\n#{"-"*(35)}\n' + \
                              f"{code_line}{RED}\n#---\n| Cause:"

    if not isinstance(line, list) and line[0] != -1 and line[2] != '':
        code_line = show_error_spot(line, full_line)
        file_name = line.source_name
        line_no = line[0]
        col = line[1]
    elif isinstance(line, list) and line[0][0] != -1 and line[0][2] != '':
        code_line = show_error_spot(line, full_line)
        file_name = line[0].source_name
        line_no = line[0][0]
        col = line[0][1]
    else:
        code_line = ""

    largest = min(max(
        [len(x) for x in f"| {text}".split('\n')] +
        [len(f"|    Line: {line_no}")] +
        [len(code_line.split('\n')[0])]
    ), 45)
    print(f'{RED}#{"-"*(largest//4)}')
    if len(template_additions) != 0:
        print(template_additions)
    _print_text(text, color=RED)
    if line[0] != -1:
        print(f'|    Line: {line_no}')
        print(f'|    File: {file_name}:{line_no}:{col}')
        if note is not None:
            print("#"+"-"*min(len(code_line.split('\n')[0]), 45))
            _print_text(f"{CODE81}{note}{RED}", color=RED)
        print("#"+"-"*min(len(code_line.split('\n')[0]), 45))
        print(f"{RESET}{code_line}")
    print(f'{RED}\\{"-"*(largest-1)}/{RESET}')
    print("\n\n\n\n")
    exit(1)


def inline_warning(text: str, line=invalid_pos):
    '''displays a warning without any special formatting encasing it.'''
    if SILENT_MODE:
        return

    print(ORANGE, end='')
    _print_text(text, color=ORANGE)
    if line[0] != -1 and line[2] != '':
        print(f'|    Line: {line.line}')
        print(f'|    File: {line.source_name}')
    print(RESET, end='')


def warning(text: str, line=invalid_pos, full_line=False):
    '''prints a warning with a line # if provided'''
    if SILENT_MODE or SUPRESSED_WARNINGS:
        return

    if line[0] != -1 and line[2] != '':
        code_line = show_error_spot(line, full_line, color=CODE214)
    else:
        code_line = ""

    largest = min(max(
        [len(x) for x in f"| {text}".split('\n')] +
        [len(f"|    Line: {line[0]}")] +
        [len(code_line.split('\n')[0])]
    ), 45)
    print(f'{CODE214}#{"-"*(largest//4)}')

    _print_text(text, color=CODE214)
    if line[0] != -1:
        print(f'|    Line: {line[0]}')
        print(f'|    File: {line.source_name}')
        print("#"+"-"*min(len(code_line.split('\n')[0]), 80))
        print(f"{RESET}{code_line}")
    print(f'{CODE214}#{"-"*(largest-1)}/{RESET}')


def developer_warning(text: str):
    '''give warnings to developers of the language that unsupported behavior
    is being used.'''
    if SILENT_MODE:
        return

    print(CODE125, end='')

    if (frame := currentframe()) is not None:
        frameinfo = getframeinfo(frame)
        _print_text(f"{text}\n\t at: {frameinfo.filename}, {frameinfo.lineno}",
                    color=CODE125)

    print(RESET, end='')


def developer_info(text):
    '''print info directed at the developer. This is profiling infomation used
    for debugging purposes'''
    if SILENT_MODE or not PROFILING:
        return

    print(CODE125, end='')
    print(f"| {text}")
    print(RESET, end='')


def experimental_warning(text: str, possible_bugs: Sequence[str]):
    '''gives a warning about the use of experimental features
    and risks involved.'''
    if SILENT_MODE:
        return
    line_size = 35
    print(CODE202, end='')
    print(f'#{"-"*(line_size)}')
    bugs = '\n'.join(('\t- '+bug for bug in possible_bugs))
    _print_text(f"EXPERIMENTAL FEATURE WARNING::\n  {text}\n\n  \
                POSSIBLE BUGS INCLUDE:\n{bugs}", color=CODE202)
    print(f'#{"-"*(line_size)}')
    print(RESET, end='')


def highlight_code(code: str) -> str:
    return highlight(code, BCLLexer(), TerminalFormatter())[:-3]


def show_error_spot(position: MultiPosition,
                    use_full_line: bool, color=RED) -> str:
    if not isinstance(position, list) and position[0] == -1:
        return ""
    elif isinstance(position, list) and position[0][0] == -1:
        return ""

    full_line = ""
    line_no = -1
    file = ""
    if isinstance(position, list):
        file = position[0].source_name
        line_no = position[0][0]
    else:
        file = position.source_name
        line_no = position[0]

    with open(file, 'r') as fp:
        for i, line in enumerate(fp):
            if not isinstance(position, list) and i == line_no-1:
                full_line = line.strip('\n')
                break
            elif isinstance(position, list) and i == line_no-1:
                full_line = line.strip('\n')
                break
    if use_full_line:
        underline = "^"*len(full_line)
    elif isinstance(position, list):
        underline = ""
        for pos in position:
            underline += " "*(pos[1]-1-len(underline)) + "^"*pos[2]
    else:
        underline = " "*(position[1]-1) + "^"*position[2]
    full_line_len = len(full_line)
    full_line = full_line.strip()
    underline = underline[full_line_len-len(full_line):]

    highlighted = highlight_code(full_line)

    return f"{color}|    {RESET}{highlighted}{color}" + \
           f"\n|    {CODE177}{underline}            {RESET}"
