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

    __slots__ = ('keywords', 'blocks', 'parens')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keywords = (
            "define", 'and', 'or', 'not', 'return',
            'if', 'while', 'else', 'break', 'continue'
        )

        self.parsing_functions = {
            "OPEN_CURLY": (self.parse_blocks, ),
            "OPEN_CURLY_USED": (self.parse_finished_blocks,),
            "expr": (self.parse_array_index, self.parse_KV_pairs, self.parse_statement, self.parse_math, self.parse_func_call,
                     self.parse_expr_list, self.parse_array_putat),
            "statement": (self.parse_statement, ),
            "statement_list": (self.parse_statement, ),
            "SUB": (self.parse_numbers, ),
            "SUM": (self.parse_numbers, ),
            "KEYWORD": (self.parse_type_names, self.parse_return_statement, self.parse_math, self.parse_keyword_literals,
                        self.parse_control_flow, self.parse_functions, self.parse_vars, self.parse_KV_pairs),
            "func_def_portion": (self.parse_functions, ),
            "kv_pair": (self.parse_expr_list, ),
            "expr_list": (self.parse_expr_list, ),
            "OPEN_PAREN": (self.parse_parenth, ),
            "OPEN_PAREN_USED": (self.parse_parenth, ),
            "paren": (self.parse_func_call,),
            "OPEN_SQUARE": (self.parse_array_literals,),
            "typeref": (self.parse_array_types,)
        }

        self.blocks = deque(((None, 0),))
        self.parens = deque(((None, 0),))

    def post_parse(self):
        '''definition inside parserbase, essentially just runs after parsing'''
        # * give warnings about experimental features
        # if errors.USES_FEATURE["array"]:
        #     errors.experimental_warning("Arrays are an experimental feature that is not complete", ("Seg-faults","compilation errors","other memory related errors"))

        if len(self.blocks) > 1: # check for unclosed blocks
            errors.error("Unclosed '{'", line = self.blocks[-1][0].pos)
        
        elif len(self.parens) > 1: # check for unclosed blocks
            errors.error("Unclosed '('", line = self.parens[-1][0].pos)

    
    def parse_finished_blocks(self):
        '''parsing finished sets of curly braces into blocks'''
        if self.check_group(0, "OPEN_CURLY_USED statement_list|statement CLOSE_CURLY"):
            if self.simple_check(1, 'statement_list'):
                self.blocks[-1][0].children = self.peek(1).value.children
            elif self.simple_check(1, 'statement'):
                self.blocks[-1][0].children = [self.peek(1).value]
            
            if self.parens[-1][0] is not None:
                tok = self._tokens[self.parens[-1][1]]
                errors.error("Unclosed '('", line=tok.pos)
            

            block = self.blocks.pop()
            self.start = self.blocks[-1][1]

            self.replace(3, "statement", block[0])

    def parse_blocks(self):
        '''Parses blocks of Curly-braces'''
        if self.simple_check(0, "OPEN_CURLY"):
            output = Ast.Block(self.peek(0).pos)


            # * check for function declaration before the block.
            # * this lets arguments be interpreted as usable variables.
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
            self._tokens[self._cursor] = ParserToken("OPEN_CURLY_USED", '{', self._tokens[self._cursor].pos, False)

    
    def parse_statement(self):
        '''Parsing statements and statement lists'''

        if self.check_group(-1, "__|OPEN_CURLY_USED expr|statement SEMI_COLON"):
            self.replace(2, "statement", self.peek(0).value)

        elif self.check_group(0, "statement statement !SEMI_COLON"):
            stmt_list = Ast.ContainerNode((-1,-1, -1))

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
    
    # * arrays

    def parse_array_literals(self):
        '''check for all nodes dealing with arrays'''
        if self.check_group(0, "OPEN_SQUARE expr_list|expr CLOSE_SQUARE") and not self.check(-1, "expr|typeref|KEYWORD"):
            exprs = self.peek(1).value if self.peek(1).name == "expr" else self.peek(1).value.children
            literal = Ast.ArrayLiteral(self.peek(0).pos, exprs)
            self.replace(3,"expr", literal)
    
    def parse_array_index(self):
        '''parse indexing of ararys'''
        if self.check_simple_group(0, "expr OPEN_SQUARE expr CLOSE_SQUARE") and \
                (isinstance(self.peek(0).value, Ast.variable.VariableRef) or isinstance(self.peek(0).value, Ast.variable.VariableIndexRef)):
            expr = self.peek(2).value
            ref = self.peek(0).value
            fin = Ast.variable.VariableIndexRef(self.peek(0).pos, ref, expr)
            self.replace(4,"expr", fin)
    
    def parse_array_putat(self):
        if self.check_group(0, "expr SET_VALUE expr SEMI_COLON") and (isinstance(self.peek(0).value, Ast.variable.VariableIndexRef)):
            ref = self.peek(0).value
            val = self.peek(2).value
            self.replace(4,"statement", Ast.variable.VariableIndexPutAt(self.peek(0).pos, ref, val))

    # * typerefs

    def parse_type_names(self):
        '''checks for type refs'''
        if self.simple_check(0, "KEYWORD") and self.peek(0).value in Ast.Ast_Types.types_dict.keys():
            val = Ast.TypeRefLiteral(self.peek(0).pos, Ast.Ast_Types.types_dict[self.peek(0).value]())
            self.replace(1,"typeref", val)
        
    def parse_array_types(self):
        '''parse typerefs with array types'''
        if self.check_simple_group(0, "typeref OPEN_SQUARE expr CLOSE_SQUARE"):
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
        
        elif self.check_group(0, "$continue SEMI_COLON"):
            x = Ast.loops.ContinueStatement(self.peek(0).pos)
            self.replace(2,"statement", x)
        
        elif self.check_group(0, "$break SEMI_COLON"):
            x = Ast.loops.BreakStatement(self.peek(0).pos)
            self.replace(2,"statement", x)
    
    
    def parse_functions(self):
        '''Function definitions'''
        # * Function Definitions
        if self.check_group(0,"KEYWORD KEYWORD expr|paren !RIGHT_ARROW"):
            if self.check(0, '$define'):
                func_name = self.peek(1).value
                block = self.peek(2).value
                func = Ast.FunctionDef(self.peek(0).pos, func_name, self.peek(2).value, block, self.module)
                self.start_min = self._cursor
                self.replace(3,"func_def_portion", func)
            elif self.peek(0).value not in self.keywords:
                error(f"invalid syntax '{self.peek(0).value}'", line = self.peek(0).pos)
        
        # * create function with return
        elif self.check_group(0,"KEYWORD KEYWORD expr|paren RIGHT_ARROW typeref !OPEN_SQUARE"):
            if self.check(0, '$define'):
                func_name = self.peek(1).value
                block = self.peek(2).value
                func = Ast.FunctionDef(self.peek(0).pos, func_name, self.peek(2).value, block, self.module)
                func.ret_type = self.peek(4).value.value
                func.is_ret_set = True
                self.start_min = self._cursor
                self.replace(5,"func_def_portion", func)
            elif self.peek(0).value not in self.keywords:
                error(f"invalid syntax '{self.peek(0).value}'", line = self.peek(0).pos)
        
        # * bug check
        elif self.check_simple_group(0,"func_def_portion RIGHT_ARROW typeref") and self.check(3, "!OPEN_SQUARE"):
            error(f"Function, \"{self.peek(0).value.name}\", cannot have it's return-type set twice.", line = self.peek(1).pos)

        # * complete function definition.
        elif self.check_simple_group(0,"func_def_portion statement"):
            self.peek(0).value.block = self.peek(1).value
            self.start_min = self._cursor
            self.replace(2,"func_def", self.peek(0).value)
            
    
    def parse_func_call(self):
        # * Function Calls
        if self.check_group(-1,"!DOT expr expr|paren") and (isinstance(self.peek(0).value, Ast.variable.VariableRef)):
            func_name = self.peek(0).value.var_name
            args = self.peek(1).value

            if not isinstance(args, Ast.nodes.ParenthBlock):
                args = Ast.nodes.ParenthBlock(self.peek(1).pos)
                args.children.append(self.peek(1).value)

            func = Ast.FunctionCall(self.peek(0).pos, func_name, args)
            self.replace(2,"expr", func)

        # * different func calls "9.to_string()" as an example
        elif self.check_group(0,"expr|paren DOT expr expr|paren") and (isinstance(self.peek(2).value, Ast.variable.VariableRef)):
            func_name = self.peek(2).value.var_name
            args1 = self.peek(0).value
            args2 = self.peek(3).value
            args1 = args1.children if isinstance(args1, Ast.nodes.ParenthBlock) else [args1] # wrap in a list if not already done
            args2 = args2.children if isinstance(args2, Ast.nodes.ParenthBlock) else [args2] # wrap in a list if not already done
            args = Ast.nodes.ParenthBlock(self.peek(0).pos)
            args.children = args1+args2
            func = Ast.FunctionCall(self.peek(2).pos, func_name, args)
            self.replace(4,"expr", func)
    
    
    def parse_KV_pairs(self):
        '''check special rules'''

        # * KV pairs
        if self.check_group(0, 'KEYWORD COLON typeref !OPEN_SQUARE'):# and (isinstance(self.peek(0).value, Ast.variable.VariableRef)):
            keywords = self.check_simple_group(0, 'KEYWORD COLON typeref')
                # error(f"A Key-Value pair cannot be created for token {self.peek(0)['name']}", line = self.peek(0).pos)
            kv = Ast.nodes.KeyValuePair(self.peek(0).pos, self.peek(0).value, self.peek(2).value, keywords = keywords)
            self.replace(3,"kv_pair", kv)
        
        if self.check_group(0, 'expr COLON typeref !OPEN_SQUARE') and (isinstance(self.peek(0).value, Ast.variable.VariableRef)):
            keywords = self.check_simple_group(0, 'expr COLON typeref')
                # error(f"A Key-Value pair cannot be created for token {self.peek(0)['name']}", line = self.peek(0).pos)
            kv = Ast.nodes.KeyValuePair(self.peek(0).pos, self.peek(0).value, self.peek(2).value, keywords = keywords)
            self.replace(3,"kv_pair", kv)
    
    def parse_keyword_literals(self):
        '''litterals like `true` and `false`, later `none`'''
        if self.check(0, '$true'):
            self.replace(1,"expr", Ast.Literal(self.peek(0).pos, 1, Ast.Ast_Types.Type_Bool.Integer_1())) #type: ignore
        elif self.check(0, '$false'):
            self.replace(1,"expr", Ast.Literal(self.peek(0).pos, 0, Ast.Ast_Types.Type_Bool.Integer_1())) #type: ignore

    def parse_return_statement(self):
        if self.check_group(0, "$return expr SEMI_COLON"):
            value = self.peek(1).value
            self.replace(3, 'statement', Ast.ReturnStatement(self.peek(0).pos, value))
    
    
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
            self.replace(4,"statement", var)
        
        # * Variable References
        elif self.blocks[-1][0]!=None and self.check_group(0,"KEYWORD !SET_VALUE") and self.check(-1, "!$define"):
            if self.peek(0).value not in self.keywords:
                var = Ast.VariableRef(self.peek(0).pos, self.peek(0).value, self.blocks[-1][0])
                self.replace(1,"expr", var)
    
    def parse_numbers(self):
        '''Parse raw integers into `expr` token.'''

        # * allow leading `+` or `-`.
        if self.check_group(-1,'!expr SUB|SUM expr') and isinstance(self.peek(1).value, Ast.Literal) and \
                self.peek(1).value.ret_type in (Ast.Ast_Types.Float_32, Ast.Ast_Types.Integer_32):
            if self.check(0,"SUB"):
                self.peek(1).value.value *= -1
                self.replace(2, "expr", self.peek(1).value)
            elif self.check(0,"SUM"):
                self.replace(2, "expr", self.peek(1).value)
    
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
    
    def parse_expr_list(self):
        # * parse expression lists
        if self.check_group(0, "expr|expr_list|kv_pair COMMA expr|kv_pair !COLON"):
            expr = self.peek(0)
            out = None
            if expr.name == "expr_list":
                expr.value.append_children(self.peek(2).value)
                out = expr.value
            else:
                out = Ast.nodes.ContainerNode((-1,-1,-1))
                out.append_child(expr.value)
                out.append_child(self.peek(2).value)
            
            self.replace(3, "expr_list", out)


    def parse_parenth(self):
        '''Parses blocks of parenthises'''        
        # * parse empty paren blocks
        if self.check_simple_group(0, "OPEN_PAREN CLOSE_PAREN"):
            self.replace(2, "paren", Ast.ParenthBlock(self.peek(0).pos))
        
        # * parse paren start
        elif self.simple_check(0, "OPEN_PAREN"):
            output = Ast.ParenthBlock(self.peek(0).pos)

            # * main implementation
            self.parens.append((output, self._cursor))

            self.start = self._cursor
            self._tokens[self._cursor] = ParserToken("OPEN_PAREN_USED", '(', self._tokens[self._cursor].pos, False)
            
        # * parse full paren blocks
        if self.check_group(0, "OPEN_PAREN_USED expr|expr_list|kv_pair CLOSE_PAREN"):
            name = "expr"

            if self.simple_check(1, 'expr_list'):
                self.parens[-1][0].children = self.peek(1).value.children
                name = "paren"
            elif self.simple_check(1, 'expr') or self.simple_check(1, 'kv_pair'):
                self.parens[-1][0].children = [self.peek(1).value]

            block = self.parens.pop()
            
            self.start = self.parens[-1][1]

            self.replace(3, name, block[0]) # return to old block
