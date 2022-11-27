import sys
from collections import deque
from typing import Callable

import Ast
import errors
from errors import error
from parserbase import ParserBase, ParserToken


class Parser(ParserBase):
    ''' The actual BCL parser implementation.
    =========================================

    Properties/Variables explained for other devs:
    - keywords:= the keywords used in the language. This prevents them from being turned into variables by the parser
    - blocks:= a `collections.deque` that stores the stack of blocks. This allows for nested blocks of curly-braces. There is also a default node.
    - parens:= a `collections.deque` that stores the stack of parens. This allows for nested sets of parenthesis. There is also a default node.
    - parsing_functions:= a dict of all the functions used for parsing. 
        This is to allow lookup of token names at the current cursor position and only run parsing functions that are relevant to that node.
    
    '''

    __slots__ = ('keywords', 'blocks', 'parens', 'parsing_functions')

    def __init__(self, *args, **kwargs):
        self.keywords = (
            "define", 'and', 'or', 'not', 'return',
            'if', 'while', 'else'
        )

        self.parsing_functions = {
            "OPEN_CURLY": (self.parse_blocks, self.parse_special, ),
            "OPEN_CURLY_USED": (self.parse_blocks,),
            "expr": (self.parse_arrays, self.check_type_names, self.parse_special, self.parse_statement, self.parse_math, self.parse_functions, self.parse_parenth),
            "statement": (self.parse_statement, ),
            "statement_list": (self.parse_statement, ),
            "NUMBER": (self.parse_numbers, ),
            "NUMBER_F": (self.parse_numbers, ),
            "SUB": (self.parse_numbers, ),
            "SUM": (self.parse_numbers, ),
            "KEYWORD": (self.check_type_names, self.parse_math, self.parse_control_flow, self.parse_functions, self.parse_special, self.parse_vars, ),
            "func_def_portion": (self.parse_functions, ),
            "kv_pair": (self.parse_parenth, ),
            "expr_list": (self.parse_parenth, ),
            "OPEN_PAREN": (self.parse_parenth, ),
            "OPEN_PAREN_USED": (self.parse_parenth, ),
            "paren": (self.parse_functions,),
            "OPEN_SQUARE": (self.parse_arrays,),
            "typeref": (self.check_type_names,)
        }

        self.blocks = deque(((None, 0),))
        self.parens = deque(((None, 0),))

        super().__init__(*args, **kwargs)

    
    def parse(self, close_condition: Callable[[],bool]=lambda: False):
        '''Parser main'''

        previous_start_position = self.start
        self.start = self._cursor   # where to reset cursor after consuming tokens.
        iters = 0

        while (not self.isEOF(self._cursor)): # and (not close_condition()):

            # * code for debugging. Use if needed
            # print(self._cursor)
            # print(',\n'.join([f'{x.name}||{x.value}' for x in self._tokens]))
            # print()
            # * end of debug code

            token_name = self.peek(0).name

            if token_name not in self.parsing_functions.keys(): # skip tokens if possible
                self.move_cursor()
                continue

            for func in self.parsing_functions[token_name]:
                func()
            

            self.move_cursor()
            iters+=1

        errors.developer_info(f"iters: {iters}")
        
        self.start = previous_start_position


        # * give warnings about experimental features
        if errors.USES_FEATURE["array"]:
            errors.experimental_warning("Arrays are an experimental feature that is not complete", ("Seg-faults","compilation errors","other memory related errors"))

        return self._tokens

    
    def parse_blocks(self):
        '''Parses blocks of Curly-braces'''
        
        # * finished block
        if self.check_group(0, "OPEN_CURLY_USED statement_list|statement CLOSE_CURLY"):
            if self.simple_check(1, 'statement_list'):
                self.blocks[-1][0].children = self.peek(1).value.children
            elif self.simple_check(1, 'statement'):
                self.blocks[-1][0].children = [self.peek(1).value]
            

            block = self.blocks.pop()
            self.start = self.blocks[-1][1]

            self.replace(3, "statement", block[0])

        # * opening of a block
        elif self.simple_check(0, "OPEN_CURLY"):
            output = Ast.Block(self.peek(0).pos)


            # * check for function declaration before the block.
            # * this lets arguments be interpreted as usable variables.
            # print(self.peek(-1))
            if self.simple_check(-1,"func_def_portion"):
                for x in self.peek(-1).value.args.keys():
                    arg = self.peek(-1).value.args[x]
                    output.variables[x] = Ast.variable.VariableObj(arg[0], arg[1].value, True)
            if self.blocks[-1][0]!=None and isinstance(self.blocks[-1][0], Ast.nodes.Block):
                for x in self.blocks[-1][0].variables.keys():
                    output.variables[x] = self.blocks[-1][0].variables[x]

            # * main implementation
            self.blocks.append((output, self._cursor))
            self.start = self._cursor
            self._tokens[self._cursor] = ParserToken("OPEN_CURLY_USED", '{', self._tokens[self._cursor].pos, self._tokens[self._cursor].completed)

    
    def parse_statement(self):
        '''Parsing statements and statement lists'''

        if self.check_group(0, "expr|statement SEMI_COLON"):
            self.replace(2, "statement", self.peek(0).value)

        elif self.check_group(0, "statement statement !SEMI_COLON"):
            stmt_list = Ast.StatementList((-1,-1, -1))

            stmt_list.append_child(self.peek(0).value)
            stmt_list.append_child(self.peek(1).value)
            self.replace(2, "statement_list", stmt_list)

        elif self.check_group(0, "statement_list statement|statement_list !SEMI_COLON"):
            stmt_list = self.peek(0).value

            stmt_list.append_children(self.peek(1).value)
            if self.blocks[-1][0] != None:
                if self.check(2,"!CLOSE_CURLY"):
                    self.start = self._cursor
                else:
                    self.start-=1
            self.replace(2, "statement_list", stmt_list)

    def parse_arrays(self):
        '''check for all nodes dealing with arrays'''

        if self.check_group(0, "OPEN_SQUARE expr_list|expr CLOSE_SQUARE") and not self.check(-1, "expr|typeref|KEYWORD"):
            errors.USES_FEATURE["array"] = True
            exprs = self.peek(1).value if self.peek(1).name == "expr" else self.peek(1).value.children
            literal = Ast.ArrayLiteral(self.peek(0).pos, exprs)
            self.replace(3,"expr", literal)
        
        if self.check_simple_group(0, "expr OPEN_SQUARE expr CLOSE_SQUARE") and (isinstance(self.peek(0).value, Ast.variable.VariableRef)):
            errors.USES_FEATURE["array"] = True
            expr = self.peek(2).value
            ref = self.peek(0).value
            fin = Ast.variable.VariableIndexRef(self.peek(0).pos, ref, expr)
            self.replace(4,"expr", fin)

    def check_type_names(self):
        '''checks for type refs'''
        if self.simple_check(0, "KEYWORD") and self.peek(0).value in Ast.Ast_Types.types_dict.keys():
            val = Ast.TypeRefLiteral(self.peek(0).pos, Ast.Ast_Types.types_dict[self.peek(0).value]())
            self.replace(1,"typeref", val)

        if self.check_simple_group(0, "typeref OPEN_SQUARE expr CLOSE_SQUARE"):
            errors.USES_FEATURE["array"] = True
            init_typ = self.peek(0).value
            typ = Ast.TypeRefLiteral(self.peek(0).pos, Ast.Ast_Types.Array(self.peek(2).value, init_typ.value, -1))
            self.replace(4,"typeref", typ)
        
        

    
    def parse_control_flow(self):
        '''parse if/then, if/else, and loops'''

        # * if blocks
        if self.check_group(0, "$if expr statement !$else"):
            expr = self.peek(1).value
            block = self.peek(2).value
            x = Ast.conditionals.IfStatement(self.peek(0).pos, expr, block)
            self.replace(3,"statement", x)

        elif self.check_group(0, "$if expr statement $else statement"):
            expr = self.peek(1).value
            block_if = self.peek(2).value
            block_else = self.peek(4).value
            x = Ast.conditionals.IfElseStatement(self.peek(0).pos, expr, block_if, block_else)
            self.replace(5,"statement", x)

        elif self.check_group(0, "$while expr statement"):
            expr = self.peek(1).value
            block = self.peek(2).value
            x = Ast.loops.WhileStatement(self.peek(0).pos, expr, block)
            self.replace(3,"statement", x)
    
    
    def parse_functions(self):
        '''Everything involving functions. Calling, definitions, etc.'''

        # * Function Definitions
        if self.check_group(0,"KEYWORD KEYWORD expr|paren"):
            if self.check(0, '$define'):
                func_name = self.peek(1).value
                block = self.peek(2).value
                func = Ast.FunctionDef(self.peek(0).pos, func_name, self.peek(2).value, block, self.module)
                self.start_min = self._cursor
                self.replace(3,"func_def_portion", func)
            elif self.peek(0).value not in self.keywords:
                error(f"invalid syntax '{self.peek(0).value}'", line = self.peek(0).pos)
        
        # * Set Function Return Type 
        elif self.check_simple_group(0,"func_def_portion RIGHT_ARROW typeref") and self.check(3, "!OPEN_SQUARE"):
            if self.peek(0).value.is_ret_set:
                error(f"Function, \"{self.peek(0).value.name}\", cannot have it's return-type set twice.", line = self.peek(1).pos)
            self.peek(0).value.ret_type = self.peek(2).value.value  # type: ignore
            self.peek(0).value.is_ret_set = True
            self.replace(3,"func_def_portion", self.peek(0).value, completed = False)

        # * complete function definition.
        elif self.check_simple_group(0,"func_def_portion statement"):
            self.peek(0).value.block = self.peek(1).value
            self.start_min = self._cursor
            self.replace(2,"func_def", self.peek(0).value)
            
        
        # * Function Calls
        elif self.check_group(0,"expr expr|paren") and (isinstance(self.peek(0).value, Ast.variable.VariableRef)):
            func_name = self.peek(0).value.name
            args = self.peek(1).value

            if not isinstance(args, Ast.nodes.ParenthBlock):
                args = Ast.nodes.ParenthBlock(self.peek(1).pos)
                args.children.append(self.peek(1).value)

            func = Ast.FunctionCall(self.peek(0).pos, func_name, args)
            self.replace(2,"expr", func)

        # * different func calls "9.to_string()" as an example
        elif self.check_group(0,"expr|paren DOT expr expr|paren") and (isinstance(self.peek(2).value, Ast.variable.VariableRef)):
            func_name = self.peek(2).value.name
            args1 = self.peek(0).value
            args2 = self.peek(3).value
            args1 = args1.children if isinstance(args1, Ast.nodes.ParenthBlock) else [args1] # wrap in a list if not already done
            args2 = args2.children if isinstance(args2, Ast.nodes.ParenthBlock) else [args2] # wrap in a list if not already done
            args = Ast.nodes.ParenthBlock(self.peek(0).pos)
            args.children = args1+args2
            func = Ast.FunctionCall(self.peek(2).pos, func_name, args)
            self.replace(4,"expr", func)
    
    
    def parse_special(self):
        '''check special rules'''

        # * KV pairs
        if self.check_group(0, 'KEYWORD COLON typeref !OPEN_SQUARE'):# and (isinstance(self.peek(0).value, Ast.variable.VariableRef)):
            keywords = self.check_simple_group(0, 'KEYWORD COLON typeref')
                # error(f"A Key-Value pair cannot be created for token {self.peek(0)['name']}", line = self.peek(0).pos)
            kv = Ast.nodes.KeyValuePair(self.peek(0).pos, self.peek(0).value, self.peek(2).value, keywords = keywords)
            self.replace(3,"kv_pair", kv)
        
        # * true and false
        elif self.check(0, '$true'):
            self.replace(1,"expr", Ast.Literal(self.peek(0).pos, 1, Ast.Ast_Types.Type_Bool.Integer_1())) #type: ignore
        elif self.check(0, '$false'):
            self.replace(1,"expr", Ast.Literal(self.peek(0).pos, 0, Ast.Ast_Types.Type_Bool.Integer_1())) #type: ignore

        elif self.check_group(0, "$return expr SEMI_COLON"):
            value = self.peek(1).value
            self.replace(3, 'statement', Ast.ReturnStatement(self.peek(0).pos, value))


        # * parse lists
        elif self.check_group(0, "OPEN_CURLY expr|expr_list CLOSE_CURLY"):
            pass
    
    
    def parse_vars(self):
        '''Parses everything involving Variables. References, Instantiation, value changes, etc.'''

        # * Variable Assignment
        if self.check_group(0,"KEYWORD SET_VALUE expr|statement SEMI_COLON"):
            # validate value
            if self.blocks[-1][0] == None:
                error("Variables cannot currently be defined outside of a block", line = self.peek(0).pos)
            elif self.simple_check(2, "statement"):
                error("A variables value cannot be set as a statement", line = self.peek(0).pos)
            var_name = self.peek(0).value
            value = self.peek(2).value
            var = Ast.VariableAssign(self.peek(0).pos, var_name, value, self.blocks[-1][0])
            self.replace(3,"statement", var)
        
        # * Variable References
        elif self.blocks[-1][0]!=None and self.check_group(0,"KEYWORD !SET_VALUE") and self.check(1, "!expr"):
            if self.peek(0).value not in self.keywords:
                var = Ast.VariableRef(self.peek(0).pos, self.peek(0).value, self.blocks[-1][0])
                self.replace(1,"expr", var)

    
    def parse_numbers(self):
        '''Parse raw integers into `expr` token.'''

        create_num = lambda x, m: Ast.Literal(self.peek(0).pos, m*int(self.peek(x).value), Ast.Ast_Types.Integer_32())  # type: ignore
        create_num_f = lambda x, m: Ast.Literal(self.peek(0).pos, m*float(self.peek(x).value.strip('f')), Ast.Ast_Types.Float_64())  # type: ignore
        
        # * Turn `NUMBER` token into an expr
        if self.simple_check(0,"NUMBER"):
            self.replace(1,"expr",create_num(0,1))

        if self.simple_check(0, "NUMBER_F"):
            self.replace(1,"expr",create_num_f(0,1))

        # * allow leading `+` or `-`.
        elif self.check_group(-1,'!expr SUB|SUM NUMBER'):
            if self.check(0,"SUB"):
                self.replace(2, "expr", create_num(1,-1))
            elif self.check(0,"SUM"):
                self.replace(2, "expr", create_num(1,1))
        
        elif self.check_group(-1,'!expr SUB|SUM NUMBER_F'):
            if self.simple_check(0,"SUB"):
                self.replace(2, "expr", create_num_f(1,-1))
            elif self.simple_check(0,"SUM"):
                self.replace(2, "expr", create_num_f(1,1))
    
    
    def parse_math(self):
        '''Parse mathematical expressions'''

        # todo: add more operations

        # * Parse expressions
        if self.check_group(0,'expr _ expr') and self.peek(1).name in Ast.math.ops.keys():
            op_str =self.peek(1).name
            op = Ast.math.ops[op_str](self.peek(0).pos, self.peek(0).value, self.peek(2).value)
            self.replace(3,"expr",op)
        
        elif self.check_group(0,'expr $and expr'):
            op = Ast.math.ops['and'](self.peek(0).pos, self.peek(0).value, self.peek(2).value)
            self.replace(3,"expr",op)
        
        elif self.check_group(0,'expr $or expr'):
            op = Ast.math.ops['or'](self.peek(0).pos, self.peek(0).value, self.peek(2).value)
            self.replace(3,"expr",op)
        
        elif self.check_group(0,'$not expr'):
            op = Ast.math.ops['not'](self.peek(0).pos, self.peek(1).value, Ast.nodes.ExpressionNode((-1,-1,-1)))
            self.replace(2,"expr",op)
    
    
    def parse_parenth(self):
        '''Parses blocks of parenthises'''

        # * parse expression lists
        if self.check_group(0, "expr|expr_list|kv_pair COMMA expr|kv_pair !COLON"):
            expr = self.peek(0)
            out = None
            if expr.name == "expr_list":
                expr.value.append_children(self.peek(2).value)
                out = expr.value
            else:
                out = Ast.nodes.ExpressionList((-1,-1,-1))
                out.append_child(expr.value)
                out.append_child(self.peek(2).value)
            
            self.replace(3, "expr_list", out)
        
        # * parse empty paren blocks
        elif self.check_simple_group(0, "OPEN_PAREN CLOSE_PAREN"):
            self.replace(2, "paren", Ast.ParenthBlock(self.peek(0).pos))
        
        # * parse paren start
        elif self.simple_check(0, "OPEN_PAREN"):
            output = Ast.ParenthBlock(self.peek(0).pos)

            # * main implementation
            self.parens.append((output, self._cursor))

            self.start = self._cursor
            self._tokens[self._cursor] = ParserToken("OPEN_PAREN_USED", '(', self._tokens[self._cursor].pos, self._tokens[self._cursor].completed)
            
        # * parse full paren blocks
        elif self.check_group(0, "OPEN_PAREN_USED expr|expr_list|kv_pair CLOSE_PAREN"):
            name = "expr"

            if self.simple_check(1, 'expr_list'):
                self.parens[-1][0].children = self.peek(1).value.children
                name = "paren"
            elif self.simple_check(1, 'expr') or self.simple_check(1, 'kv_pair'):
                self.parens[-1][0].children = [self.peek(1).value]

            block = self.parens.pop()
            
            self.start = self.parens[-1][1]

            self.replace(3, name, block[0]) # return to old block
