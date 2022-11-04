import sys
from collections import deque
from typing import Callable

import Ast
import errors
from errors import error
from parserbase import ParserBase, ParserToken


class parser(ParserBase):
    __slots__ = ('statements', 'keywords', 'simple_rules', 'current_block', 'blocks', 'current_paren', 'parens', 'skippable_tokens', 'parsing_functions')

    def __init__(self, *args, **kwargs):
        self.statements = (
            'return', 'if', 'while', 'else'
        )
        self.keywords = (
            "define", "return", 'if', 'else', 'and', 'or', 'not', 'while'
        )

        self.parsing_functions = { # functions used for parsing. Put into a tuple based on the starting tokens of their rules
            "OPEN_CURLY": (self.parse_blocks, self.parse_special, ),
            "OPEN_CURLY_USED": (self.parse_blocks,),
            "expr": (self.parse_statement, self.parse_math, self.parse_functions, self.parse_parenth, ),
            "statement": (self.parse_statement, ),
            "statement_list": (self.parse_statement, ),
            "NUMBER": (self.parse_numbers, ),
            "NUMBER_F": (self.parse_numbers, ),
            "SUB": (self.parse_numbers, ),
            "SUM": (self.parse_numbers, ),
            "KEYWORD": (self.parse_math, self.parse_control_flow, self.parse_functions, self.parse_special, self.parse_vars, ),
            "func_def_portion": (self.parse_functions, ),
            "kv_pair": (self.parse_parenth, ),
            "expr_list": (self.parse_parenth, ),
            "OPEN_PAREN": (self.parse_parenth, ),
            "OPEN_PAREN_USED": (self.parse_parenth, ),
            "paren": (self.parse_functions,)
        }

        self.current_block: tuple[Ast.StatementList|Ast.Block, int] = (None, 0)  # type: ignore
        self.blocks        = deque()

        self.current_paren: tuple[Ast.ExpressionList|Ast.ParenthBlock, int] = (None, 0)  # type: ignore
        self.parens        = deque()

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

            # self.parse_blocks()
            # self.parse_statement()
            # self.parse_numbers()
            # self.parse_math()
            # self.parse_control_flow()
            # self.parse_functions()
            # self.parse_special() # must be before self.parse_vars
            # self.parse_vars()
            # self.parse_parenth()

            functions = self.parsing_functions[token_name]

            for func in functions:
                func()
            

            self.move_cursor()
            iters+=1

        errors.output_profile_info(f"iters: {iters}")
        
        self.start = previous_start_position

        return self._tokens

    
    def parse_blocks(self):
        '''Parses blocks of Curly-braces'''
        
        # * finished block
        if self.check_group(0, "OPEN_CURLY_USED statement_list|statement CLOSE_CURLY"):
            old_block = self.blocks.pop()
            
            self.start = old_block[1]

            if self.simple_check(1, 'statement_list'):
                self.current_block[0].children = self.peek(1).value.children
            elif self.simple_check(1, 'statement'):
                self.current_block[0].children = [self.peek(1).value]

            self.replace(3, "statement", self.current_block[0]) # return to old block
            self.current_block = old_block

        # * opening of a block
        elif self.simple_check(0, "OPEN_CURLY"):
            output = Ast.Block(self.peek(0).pos)


            # * check for function declaration before the block.
            # * this lets arguments be interpreted as usable variables.
            if self.simple_check(-1,"func_def_portion"):
                for x in self.peek(-1).value.args.keys():
                    arg = self.peek(-1).value.args[x]
                    output.variables[x] = Ast.variable.VariableObj(arg[0], arg[1], True)
            if self.current_block[0]!=None and isinstance(self.current_block[0], Ast.nodes.Block):
                for x in self.current_block[0].variables.keys():
                    output.variables[x] = self.current_block[0].variables[x]

            # * main implementation
            self.blocks.append(self.current_block)
            self.current_block = (output, self._cursor)
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
            if self.current_block[0] != None:
                if self.check(2,"!CLOSE_CURLY"):
                    self.start = self._cursor
                else:
                    self.start-=1
            self.replace(2, "statement_list", stmt_list)

    
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
        elif self.check_simple_group(0,"func_def_portion RIGHT_ARROW KEYWORD"):
            if self.peek(0).value.is_ret_set:
                error(f"Function, \"{self.peek(0).value.name}\", cannot have it's return-type set twice.", line = self.peek(0).pos)
            self.peek(0).value.ret_type = Ast.Ast_Types.Type_Base.types_dict[self.peek(2).value]()  # type: ignore
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
        if self.check_group(0, '_ COLON _'):
            keywords = self.check_simple_group(0, 'KEYWORD COLON KEYWORD')
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
            if self.current_block[0] == None:
                error("Variables cannot currently be defined outside of a block", line = self.peek(0).pos)
            elif self.simple_check(2, "statement"):
                error("A variables value cannot be set as a statement", line = self.peek(0).pos)
            var_name = self.peek(0).value
            value = self.peek(2).value
            var = Ast.VariableAssign(self.peek(0).pos, var_name, value, self.current_block[0])
            self.replace(3,"statement", var)
        
        # * Variable References
        elif self.current_block[0]!=None and self.check_group(0,"KEYWORD !SET_VALUE") and self.check(1, "!expr"):
            if self.peek(0).value not in self.keywords:#self.current_block[0].variables.keys():
                var = Ast.VariableRef(self.peek(0).pos, self.peek(0).value, self.current_block[0])
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
        if self.check_group(0, "expr|expr_list|kv_pair COMMA expr|kv_pair"):
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
            self.parens.append(self.current_paren)
            self.current_paren = (output, self._cursor)
            self.start = self._cursor
            self._tokens[self._cursor] = ParserToken("OPEN_PAREN_USED", '(', self._tokens[self._cursor].pos, self._tokens[self._cursor].completed)
            
        # * parse full paren blocks
        elif self.check_group(0, "OPEN_PAREN_USED expr|expr_list CLOSE_PAREN"):
            old_block = self.parens.pop()
            
            self.start = old_block[1]
            name = "expr"

            if self.simple_check(1, 'expr_list'):
                self.current_paren[0].children = self.peek(1).value.children
                name = "paren"
            elif self.simple_check(1, 'expr'):
                self.current_paren[0].children = [self.peek(1).value]

            self.replace(3, name, self.current_paren[0]) # return to old block
            self.current_paren = old_block
