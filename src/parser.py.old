from rply import ParserGenerator
from Ast import *
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
        self.program = Blocks.Program(builder,module)

        self.functions = {
            "print" : Functions.Print,
            "println" : Functions.Println
        }

    def parse(self):
        @self.pg.production('program : block')
        @self.pg.production('program : program func')
        def program(p):
            #print(p)
            self.program.append(p[0])
            return self.program
        
        @self.pg.production('block : func SEMI_COLON')
        @self.pg.production('block : block func SEMI_COLON')
        def block(p):
            #print(p)
            if len(p)==3:
                p[0].append(p[1])
                return p[0]
            x=Blocks.Block()
            x.append(p[0])
            return x
        
        @self.pg.production('func : KEYWORD paren')
        #@self.pg.production('func : block KEYWORD paren')
        def func(p):
            if p[-2].value in self.functions.keys():
                return self.functions[p[-2].value](self.program, self.printf, p[-1], p[-2].getsourcepos().lineno)
            Errors.Error.Unknown_Function(p[-2].source_pos.lineno)

        @self.pg.production('expression : expression SUM expression')
        @self.pg.production('expression : expression SUB expression')
        def expression(p):
            left = p[0]
            right = p[2]
            operator = p[1]
            if operator.gettokentype() == 'SUM':
                return Math.Sum(self.program, left, right)
            elif operator.gettokentype() == 'SUB':
                return Math.Sub(self.program, left, right)

        @self.pg.production('list : expression')
        @self.pg.production('list : list COMMA expression')
        def paren_open(p):
            if len(p)==3:
                p[0].append(p[2])
                return p[0]
            x=Blocks.Parenth()
            x.append(p[0])
            return x

        @self.pg.production('paren : OPEN_PAREN list CLOSE_PAREN')
        def paren(p):
            return p[1]

        @self.pg.production('expression : NUMBER')
        @self.pg.production('expression : STRING')
        def number(p):
            if p[0].gettokentype() == 'NUMBER':
                return Integers.Int_32(p[0].value, self.program)
            else:
                return MiscTypes.String_utf8(self.builder, self.module, p[0].value)

        @self.pg.error
        def error_handle(token):
            #print(dir(token))
            Errors.Error.Unknown(token.getstr(),token.getsourcepos().lineno)

    def get_parser(self):
        return self.pg.build()