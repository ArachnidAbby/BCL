from rply import LexerGenerator


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
        # Semi Colon, comma, etc
        self.lexer.add('SEMI_COLON', r'\;')
        self.lexer.add('COLON', r'\:')
        self.lexer.add('COMMA', r'\,')
        # Operators
        self.lexer.add('SUM', r'\+')
        self.lexer.add('MUL', r'\*')
        self.lexer.add('DIV', r'/{1,}')
        self.lexer.add('SUB', r'\-')
        self.lexer.add('MOD', r'\%') 
        self.lexer.add('EQ', r'\=\=') 
        self.lexer.add('SET_VALUE', r'\=')
        # Number
        self.lexer.add('NUMBER', r'\d+')
        self.lexer.add('NUMBER_F', r'\d+((\.\d+f)|(\.\d+)|f)')
        # Keywords and strings
        self.lexer.add('STRING',r'\"(\\.|[^"\\])*\"')
        self.lexer.add('KEYWORD', r'(\w+)')
        # Ignore spaces
        self.lexer.ignore(r'\s+')
        self.lexer.ignore(r'//.*')

    def get_lexer(self):
        self._add_tokens()
        return self.lexer.build()
