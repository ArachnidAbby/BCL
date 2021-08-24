from rply import ParserGenerator
from ast import Number, Sum, Sub, Print, Program, Println, Parenth,String_utf8
import Errors


class Parser():
    def __init__(self, module, builder, printf):
        self.pg = ParserGenerator(
            # A list of all token names accepted by the parser.
            ['NUMBER', 'OPEN_PAREN', 'CLOSE_PAREN',
             'SEMI_COLON', 'SUM', 'SUB','KEYWORD','COMMA','STRING']
        )
        self.module = module
        self.builder = builder
        self.printf = printf
        self.program = Program(builder,module)

        self.functions = {
            "print" : Print,
            "println" : Println
        }

    def parse(self):
        @self.pg.production('program : func')
        @self.pg.production('program : program func')
        def program(p):
            #print(p)
            self.program.append(p[0])
            return self.program


        @self.pg.production('func : KEYWORD paren SEMI_COLON')
        @self.pg.production('func : program KEYWORD paren SEMI_COLON')
        def func(p):
            if p[-3].value in self.functions.keys():
                return self.functions[p[-3].value](self.program, self.printf, p[-2], p[-3].getsourcepos().lineno)
            Errors.Error.Unknown_Function(p[-3].source_pos.lineno)

        @self.pg.production('expression : expression SUM expression')
        @self.pg.production('expression : expression SUB expression')
        def expression(p):
            left = p[0]
            right = p[2]
            operator = p[1]
            if operator.gettokentype() == 'SUM':
                return Sum(self.builder, self.module, left, right)
            elif operator.gettokentype() == 'SUB':
                return Sub(self.builder, self.module, left, right)

        @self.pg.production('paren_open : OPEN_PAREN expression')
        @self.pg.production('paren_open : paren_open COMMA expression')
        def paren_open(p):
            if len(p)==3:
                p[0].append(p[2])
                return p[0]
            x=Parenth()
            x.append(p[1])
            return x

        @self.pg.production('paren : paren_open CLOSE_PAREN')
        def paren(p):
            return p[0]

        @self.pg.production('expression : NUMBER')
        @self.pg.production('expression : STRING')
        def number(p):
            #print(p)
            if p[0].gettokentype() == 'NUMBER':
                return Number(self.builder, self.module, p[0].value)
            else:
                return String_utf8(self.builder, self.module, p[0].value)

        @self.pg.error
        def error_handle(token):
            #print(dir(token))
            Errors.Error.Unknown(token.getstr(),token.getsourcepos().lineno)

    def get_parser(self):
        return self.pg.build()