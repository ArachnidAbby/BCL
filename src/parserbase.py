import ast  # python ast module
from typing import Any, Callable, NamedTuple, Self

import Ast
import errors
from Ast.literals.numberliteral import Literal
from Ast.literals.stringliteral import StrLiteral
from Ast.nodes.commontypes import SrcPosition


def fix_char(val) -> int:
    return ord(val.encode('raw_unicode_escape').decode('unicode_escape'))


def fix_str(val) -> str:
    return ast.literal_eval(val)+'\0'


class ParserToken(NamedTuple):
    # __slots__ = ('name', 'value', 'source_pos', 'completed')

    name: str
    value: Any
    source_pos: tuple[int, int, int, str]  # TODO: Make into named tuple
    completed: bool

    @property
    def pos(self):
        return self.source_pos


# Max amount of preloaded tokens that are ahead of the cursor
MAX_SIZE = 8  # TODO: move this into the ParserBase class


class ParserBase:
    __slots__ = ('_tokens', '_cursor', 'start', 'builder', 'module', 'do_move',
                 'start_min', 'parsing_functions', 'standard_expr_checks',
                 'op_node_names', 'compiled_rules', 'lex_stream', 'EOS')
    '''Backend of the Parser.
        This is primarily to seperate the basics of parsing from the actual
        parser for the language.
    '''

    CREATED_RULES: list[tuple[str, int]] = []

    def __init__(self, lex_stream, module):
        self._tokens = []
        self.lex_stream = lex_stream
        self._cursor = 0
        self.start = 0
        self.module = module
        self.do_move = True
        self.EOS = False
        self.start_min = 0
        self.parsing_functions = {}
        self.standard_expr_checks = ("OPEN_PAREN", "DOT", "KEYWORD",
                                     "expr", "OPEN_SQUARE", "paren")
        self.op_node_names = ("SUM", "SUB", "MUL", "DIV", "MOD",
                              "COLON", "DOUBLE_DOT")
        self.compiled_rules: dict[str, Callable[Self, bool]] = {}

        for rule, start in self.CREATED_RULES:
            self.compiled_rules[rule] = self.compile_rule(rule)

        del self.CREATED_RULES[0:]  # clear unused memory

    def single_compile(self, wanting: str, pos: int) -> str:
        if wanting == '_':  # allow any
            return 'True'
        if wanting == '__':  # allow any with "complete" == True
            return f'input[{pos}].completed'
        elif wanting.startswith('!'):  # `not` operation
            return f'(not {self.single_compile(wanting[1:], pos)})'
        elif wanting.startswith('$'):  # `match value` operation
            return f'input[{pos}].value=="{wanting[1:]}"'
        elif '|' in wanting:  # `or` operation
            return "("+(' or '.join([self.single_compile(y, pos) for y in wanting.split('|')]))+")"
        else:
            return f'input[{pos}].name=="{wanting}"'

    def compile_rule(self, rule: str) -> tuple[Callable[[list[ParserToken]], bool], int]:
        output_stmts: list[str] = []
        for c, wanting in enumerate(rule.split(' ')):
            if wanting == '_':  # allow any
                continue
            output_stmts.append(self.single_compile(wanting, c))

        output_str = (" and ".join(output_stmts))

        return (compile(output_str, 'COMPILED RULE', 'eval'),
                len(rule.split(' ')))

    def parse(self, close_condition: Callable[[], bool] = lambda: False):
        '''Parser main'''
        previous_start_position = self.start
        self.start = self._cursor   # where to reset cursor after consuming
        iters = 0
        self.gen_ahead(MAX_SIZE)
        while (not self.isEOF(self._cursor)):  # and (not close_condition()):
            # * code for debugging. Use if needed
            # print(self._cursor)
            # print(',\n'.join([f'{x.name}||{x.value}' for x in self._tokens]))
            # print()
            # * end of debug code
            token_name = self.peek(0).name
            # skip tokens if possible
            valid_funcs = self.parsing_functions.get(token_name)
            if not valid_funcs:  # None check
                self.move_cursor()
                continue

            for func in valid_funcs:
                func()
                if not self.do_move:
                    break

            self.move_cursor()
            iters += 1

        errors.developer_info(f"iters: {iters}")
        self.start = previous_start_position

        self.post_parse()

        return self._tokens

    def post_parse(self):
        '''steps that happen after parsing has finished.
        Used to check for syntax errors, give warnings, etc.'''

    def isEOF(self, index) -> bool:
        '''Checks if the End-Of-File has been reached'''
        return self.EOS and index >= (len(self._tokens))

    def move_cursor(self, index: int = 1):
        '''Moves the cursor unless `!self.doMove` '''
        if self.do_move:
            tokens_left = (len(self._tokens)-self._cursor)
            if tokens_left < MAX_SIZE:
                self.gen_ahead(tokens_left % MAX_SIZE)
            self._cursor += index
        self.do_move = True

    def peek(self, index: int) -> ParserToken:
        '''peek into the token list and fetch a token'''
        return self._tokens[self._cursor+index]

    def gen_ahead(self, amount) -> bool:
        '''Tells the lexer to tokenize the next tokens.
        If True is returned, all tokens were successfully fetched.
        If False is returned, all tokens were not sucessfully fetched
        '''
        for c, tok in enumerate(self.lex_stream):
            pos = SrcPosition(tok.source_pos.lineno, tok.source_pos.colno,
                              len(tok.value), self.module.location)
            if tok.name == "NUMBER":
                val = Literal(pos, int(tok.value), Ast.Ast_Types.Integer_32())
                fintok = ParserToken("expr", val, pos, True)
            elif tok.name == "NUMBER_F":
                val = Literal(pos, float(tok.value.strip('f')),
                              Ast.Ast_Types.Float_32())
                fintok = ParserToken("expr", val, pos, True)
            elif tok.name == "CHAR":
                val = Literal(pos, fix_char(tok.value.strip('\'')),
                              Ast.Ast_Types.Char())
                fintok = ParserToken("expr", val, pos, True)
            elif tok.name == "STRING":
                val = StrLiteral(pos, fix_str(tok.value))  # type: ignore
                fintok = ParserToken("expr", val, pos, True)
            else:
                fintok = ParserToken(tok.name, tok.value, pos, False)
            self._tokens.append(fintok)
            if c == amount-1:
                return True
        self.EOS = True
        return False

    def peek_safe(self, index: int) -> ParserToken:
        '''peek into the token list and fetch a token if
        overindexing the token list, it will return an empty token'''
        if self.isEOF(self._cursor+index):
            return ParserToken("EOF", "EOF", SrcPosition.invalid(), False)

        return self.peek(index)

    def _consume(self, index: int, amount: int):
        '''consume specific amount of tokens but don't reset cursor position'''
        index = self._cursor+index
        del self._tokens[index: index+amount]

    # todo: make this just use positional arguments for the amount.

    def consume(self, index: int, amount: int):
        '''Consume a specific `amount` of tokens starting at `index`'''
        self._consume(index=index, amount=amount)

        self._cursor = max(self.start, self.start_min)
        self.do_move = False

    def insert(self, index: int, name: str, value: Ast.nodes.ASTNode,
               completed=True):
        '''insert tokens at a specific location'''
        self._tokens.insert(index+self._cursor, ParserToken(name, value,
                                                            value.position,
                                                            completed))

    def check(self, index: int, wanting: str) -> bool:
        '''check the value of a token (with formatting)'''
        return eval(self.compiled_rules[wanting][0], {},
                    {"input": [self.peek(index)]})

    def simple_check(self, index: int, wanting: str) -> bool:
        '''check the value of a token (without formatting)'''
        return self.peek(index=index).name == wanting

    def replace(self, leng: int, name: str, value, i: int = 0,
                completed: bool = True):
        '''replace a group of tokens with a single token.'''
        self._consume(amount=leng, index=-i)
        self.insert(i, name, value, completed=completed)

        self._cursor = max(self.start, self.start_min)
        self.do_move = False

    def check_group(self, start_index: int, wanting: str) -> bool:
        '''check a group of tokens in a string seperated by spaces.'''
        tokens = wanting.split(' ')

        rule_max_cursor_pos = len(tokens) + self._cursor + start_index-1
        if (self._cursor+start_index) < 0 or self.isEOF(rule_max_cursor_pos):
            return False

        tokens_start = start_index + self._cursor
        tokens_end = self.compiled_rules[wanting][1] + start_index+self._cursor
        input_tokens = self._tokens[tokens_start:tokens_end]
        return eval(self.compiled_rules[wanting][0], {},
                    {"input": input_tokens})

    def check_group_lookahead(self, start_index: int, wanting: str,
                              include_ops=False) -> bool:
        '''check a group of tokens in a string seperated by spaces.
        This version has lookahead'''
        worked = self.check_group(start_index, wanting)
        if not worked:
            return False

        items = wanting.split(" ")
        if include_ops:
            return self.peek(len(items)+start_index).name not in \
                (*self.op_node_names, *self.standard_expr_checks)
        return self.peek(len(items)+start_index).name not in \
            self.standard_expr_checks

    def check_simple_group(self, start_index: int, wanting: str) -> bool:
        '''check a group of tokens in a string seperated by spaces.
        (unformatted)'''
        tokens = wanting.split(' ')

        if (len(tokens)+self._cursor+start_index) > len(self._tokens):
            return False

        for c, token in enumerate(tokens):
            if not self.simple_check(c + start_index, token):
                return False

        return True


def rule(start: int, rule: str):
    ParserBase.CREATED_RULES.append((rule, start))

    def decorator(func):
        def wrapper(self):
            if self.check_group(start, rule):
                func(self)
        return wrapper
    return decorator
