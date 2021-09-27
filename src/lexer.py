from rply import LexerGenerator


class Lexer():
    def __init__(self):
        self.lexer = LexerGenerator()

    def _add_tokens(self):
        # # Print
        # self.lexer.add('PRINT', r'println')
        # Parenthesis
        self.lexer.add('OPEN_PAREN', r'\(')
        self.lexer.add('CLOSE_PAREN', r'\)')
        # Semi Colon, comma, etc
        self.lexer.add('SEMI_COLON', r'\;')
        self.lexer.add('COMMA', r'\,')
        # Operators
        self.lexer.add('SUM', r'\+')
        self.lexer.add('SUB', r'\-')
        # Number
        self.lexer.add('NUMBER', r'\d+')
        # Keywords and strings
        self.lexer.add('STRING',r'\"(\\.|[^"\\])*\"')
        self.lexer.add('KEYWORD', r'(\w+)')
        # Ignore spaces
        self.lexer.ignore('\s+')
        self.lexer.ignore('//.*')

    def get_lexer(self):
        self._add_tokens()
        return self.lexer.build()