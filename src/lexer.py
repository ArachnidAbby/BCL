from typing import List

from rply import LexerGenerator

import Ast
from parserbase import ParserToken


class Lexer():
    '''Lexer created using the `rply.LexerGenerator`'''
    def __init__(self):
        self.lexer = LexerGenerator()

    def _add_tokens(self):
        # Parenthesis
        self.lexer.add('OPEN_PAREN', r'\(')
        self.lexer.add('CLOSE_PAREN', r'\)')
        # curly braces
        self.lexer.add('OPEN_CURLY', r'\{')
        self.lexer.add('CLOSE_CURLY', r'\}')
        # curly braces
        self.lexer.add('OPEN_SQUARE', r'\[')
        self.lexer.add('CLOSE_SQUARE', r'\]')
        # Number
        self.lexer.add('NUMBER_F', r'\d+((\.\d+f)|(\.\d+)|f)')
        self.lexer.add('NUMBER', r'\d+')
        # Semi Colon, comma, etc
        self.lexer.add('SEMI_COLON', r'\;')
        self.lexer.add('COLON', r'\:')
        self.lexer.add('RIGHT_ARROW', r'\-\>')
        self.lexer.add('COMMA', r'\,')
        self.lexer.add('DOT', r'\.')
        # Operators
        self.lexer.add('SUM', r'\+')
        self.lexer.add('MUL', r'\*')
        self.lexer.add('DIV', r'/{1,}')
        self.lexer.add('SUB', r'\-')
        self.lexer.add('MOD', r'\%') 
        self.lexer.add('EQ', r'\=\=')
        self.lexer.add('NEQ', r'\!\=')
        self.lexer.add('GEQ', r'\>\=')
        self.lexer.add('LEQ', r'\<\=')
        self.lexer.add('GR', r'\>')
        self.lexer.add('LE', r'\<')
        self.lexer.add('SET_VALUE', r'\=')
        # Keywords and strings
        self.lexer.add('STRING',r'\"(\\.|[^"\\])*\"')
        self.lexer.add('KEYWORD', r'(\w+)')
        # Ignore spaces
        self.lexer.ignore(r'\s+')
        self.lexer.ignore(r'//.*')

    def get_lexer(self):
        self._add_tokens()
        return self.lexer.build()

def get_tokens(src: str) -> List[ParserToken]:
    '''Take source and convert to a list of 'ParserToken' Objects'''
    lexer = Lexer().get_lexer()
    tokens = lexer.lex(src)
    output  = []
    for x in tokens:
        pos = (x.source_pos.lineno, x.source_pos.colno, len(x.value))
        if x.name == "NUMBER":
            val = Ast.Literal(pos, int(x.value), Ast.Ast_Types.Integer_32())
            tok = ParserToken("expr", val, pos, True)
        elif x.name == "NUMBER_F":
            val = Ast.Literal(pos, float(x.value), Ast.Ast_Types.Float_32())
            tok = ParserToken("expr", val, pos, True)
        else: tok = ParserToken(x.name, x.value, pos, False)
        output.append(tok)
    
    return output
