from collections import deque
from os import path

import Ast
import Ast.literals.numberliteral
import errors
from Ast.nodes.commontypes import SrcPosition
from errors import error
from parserbase import ParserBase, ParserToken, rule


class Parser(ParserBase):
    ''' The actual BCL parser implementation.
    =========================================

    Properties/Variables explained for other devs:
    - keywords:= the keywords used in the language.
      This prevents them from being turned into variables by the parser
    - blocks:= a `collections.deque` that stores the stack of blocks.
      This allows for nested blocks of curly-braces.
      There is also a default node.
    - parens:= a `collections.deque` that stores the stack of parens.
      This allows for nested sets of parenthesis. There is also a default node.
    - parsing_functions:= a dict of all the functions used for parsing.
      This is to allow lookup of token names at the current cursor position and
        only run parsing functions that are relevant to that node.
    '''

    __slots__ = ('keywords', 'blocks', 'parens', "standard_expr_checks",
                 "op_node_names")

    def __init__(self, *args, **kwargs):
        # * rules that aren't denoted with @rule()
        ParserBase.CREATED_RULES.append(("$true", 0))
        ParserBase.CREATED_RULES.append(("$false", 0))
        ParserBase.CREATED_RULES.append(("$TWO_PI", 0))
        ParserBase.CREATED_RULES.append(("$HALF_PI", 0))
        ParserBase.CREATED_RULES.append(("$PI", 0))
        ParserBase.CREATED_RULES.append(("CLOSE_SQUARE|expr|paren", -1))
        ParserBase.CREATED_RULES.append(("$not expr|paren", 0))
        ParserBase.CREATED_RULES.append(("expr|paren ISUM expr|paren SEMI_COLON", 0))
        ParserBase.CREATED_RULES.append(("expr|paren ISUB expr|paren SEMI_COLON", 0))
        ParserBase.CREATED_RULES.append(("expr|paren IMUL expr|paren SEMI_COLON", 0))
        ParserBase.CREATED_RULES.append(("expr|paren IDIV expr|paren SEMI_COLON", 0))
        ParserBase.CREATED_RULES.append(("expr|paren _ expr|paren", 0))
        ParserBase.CREATED_RULES.append(("expr|paren $and expr|paren", 0))
        ParserBase.CREATED_RULES.append(("expr|paren $or expr|paren", 0))
        ParserBase.CREATED_RULES.append(("expr|paren $as expr|paren", 0))
        ParserBase.CREATED_RULES.append(("$define", 0))
        ParserBase.CREATED_RULES.append(("!CLOSE_CURLY", 2))
        ParserBase.CREATED_RULES.append(("SUB", 0))
        ParserBase.CREATED_RULES.append(("SUM", 0))
        ParserBase.CREATED_RULES.append(("statement_list|expr_list", 1))

        super().__init__(*args, **kwargs)
        self.keywords = (
            "define", 'and', 'or', 'not', 'return',
            'if', 'while', 'else', 'break', 'continue',
            'as', 'for', 'in', 'struct', 'import', 'yield'
        )  # ? would it make sense to put these in a language file?

        self.standard_expr_checks = ("OPEN_PAREN", "DOT", "KEYWORD",
                                     "expr", "OPEN_SQUARE", "paren")
        self.op_node_names = ("SUM", "SUB", "MUL", "DIV", "MOD",
                              "COLON", "DOUBLE_DOT")

        self.parsing_functions = {
            "OPEN_CURLY": (self.parse_block_empty, self.parse_block_open),
            "OPEN_CURLY_USED": (self.parse_finished_blocks,
                                self.parse_struct_literal),
            "expr": (self.parse_var_decl, self.parse_array_index,
                     self.parse_KV_pairs, self.parse_statement,
                     self.parse_math, self.parse_func_call,
                     self.parse_expr_list,
                     self.parse_rangelit,
                     self.parse_member_access),
            "statement": (self.parse_statement, self.parse_combine_statements),
            "statement_list": (self.parse_statement_list, ),
            "SUB": (self.parse_numbers, ),
            "SUM": (self.parse_numbers, ),
            "KEYWORD": (self.parse_return_statement, self.parse_math,
                        self.parse_import_statment,
                        self.parse_yield_stmt,
                        self.parse_keyword_literals,
                        self.parse_if_statement,
                        self.parse_if_else,
                        self.parse_while_loop,
                        self.parse_for_loop,
                        self.parse_continue_stmt,
                        self.parse_break_stmt,
                        self.parse_var_usage, self.parse_functions,
                        self.parse_func_with_return,
                        self.parse_func_double_return,
                        self.parse_structs, self.parse_KV_pairs),
            "func_def_portion": (self.parse_funcdef_empty,
                                 self.parse_funcdef_with_body),
            "kv_pair": (self.parse_expr_list, self.parse_vardecl_explicit,
                        self.parse_statement),
            "expr_list": (self.parse_expr_list, self.parse_statement),
            "OPEN_PAREN": (self.parse_paren_empty, self.parse_paren_start),
            "OPEN_PAREN_USED": (self.parse_paren_close, ),
            "paren": (self.parse_member_access,),
            "OPEN_SQUARE": (self.parse_array_literal_multi_element,
                            self.parse_array_literal,),
            "AMP": (self.parse_varref, )
        }

        self.blocks = deque(((None, 0),))
        self.parens = deque(((None, 0),))

    def post_parse(self):
        '''definition inside parserbase, essentially just runs after parsing'''

        if len(self.blocks) > 1:  # check for unclosed blocks
            found = False
            for x in self._tokens[self.blocks[-1][1]:]:
                if x.name == "CLOSE_CURLY":
                    found = True
                    break

            if not found:
                errors.developer_info(f"{self._tokens}")
                errors.error("Unclosed '{'", line=self.blocks[-1][0].position)

        elif len(self.parens) > 1:  # check for unclosed parens
            found = False
            for x in self._tokens[self.parens[-1][1]:]:
                if x.name == "CLOSE_PAREN":
                    found = True
                    break

            if not found:
                errors.developer_info(f"{self._tokens}")
                errors.error("Unclosed '('", line=self.parens[-1][0].position)

    @rule(0, "$import expr SEMI_COLON")
    def parse_import_statment(self):
        if not isinstance(self.peek(1).value,
                          Ast.variables.reference.VariableRef):
            errors.error("Import must use a module name",
                         line=self.peek(1).pos)

        name = self.peek(1).value.var_name
        directories = self.module.location.split("/")[:-1]
        directory_path = '/'.join(directories)
        filedir = f"{directory_path}/{name}.bcl"
        if not path.exists(filedir):
            libbcl_dir = path.dirname(__file__) + "/libbcl"
            filedir = f"{libbcl_dir}/{name}.bcl"
            if not path.exists(filedir):
                errors.error(f"Could not find module '{name}'",
                             line=self.peek(1).pos)

        self.module.add_import(filedir, name)
        errors.inline_warning("Notice: import statements may be buggy")
        self.consume(0, 3)

    @rule(0, "OPEN_CURLY_USED statement_list|statement CLOSE_CURLY")
    def parse_finished_blocks(self):
        '''parsing finished sets of curly braces into blocks'''
        if self.check(1, 'statement_list|expr_list'):
            self.blocks[-1][0].children = self.peek(1).value.children
        elif self.simple_check(1, 'statement'):
            self.blocks[-1][0].children = [self.peek(1).value]

        if self.parens[-1][0] is not None:
            tok = self._tokens[self.parens[-1][1]]
            errors.developer_info(f'{self._tokens}')
            errors.error("Unclosed '('", line=tok.pos)

        block = self.blocks.pop()
        if self.blocks[-1][0] is not None:
            block[0].parent = self.blocks[-1][0]
        self.start = self.blocks[-1][1]

        self.replace(3, "statement", block[0])

    @rule(0, "OPEN_CURLY CLOSE_CURLY")
    def parse_block_empty(self):
        output = Ast.Block(self.peek(0).pos)
        if self.parens[-1][0] is not None:
            tok = self._tokens[self.parens[-1][1]]
            errors.developer_info(f'{self._tokens}')
            errors.error("Unclosed '('", line=tok.pos)

        # TODO: THIS CODE SHOULD NOT BE PLACED IN THE PARSER
        if self.simple_check(-1, "func_def_portion"):
            for x in self.peek(-1).value.args.keys():
                arg = self.peek(-1).value.args[x]
                output.variables[x] = Ast.variables.VariableObj(arg[0], arg[1],
                                                                True)

        self.replace(2, "statement", output)

    @rule(0, "OPEN_CURLY")
    def parse_block_open(self):
        output = Ast.Block(self.peek(0).pos)

        # * main implementation
        self.blocks.append((output, self._cursor))
        self.start = self._cursor
        new_token = ParserToken("OPEN_CURLY_USED", '{',
                                self._tokens[self._cursor].pos,
                                False)
        self._tokens[self._cursor] = new_token

    @rule(-1, "expr OPEN_CURLY_USED expr_list|kv_pair CLOSE_CURLY")
    def parse_struct_literal(self):
        # if isinstance(self.peek(1).value, Ast.Block):
        block = self.blocks.pop()
        if self.blocks[-1][0] is not None:
            block[0].parent = self.blocks[-1][0]

        values = self.peek(1).value
        if self.peek(1).name == "kv_pair":
            values = Ast.nodes.ContainerNode(self.peek(1).pos)
            values.append_child(self.peek(1).value)
        self.start = self.blocks[-1][1]
        struct_literal = Ast.StructLiteral(self.peek(-1).pos,
                                           self.peek(-1).value,
                                           values)
        self.replace(4, "expr", struct_literal, i=-1)

    @rule(-1, "__|OPEN_CURLY_USED expr|kv_pair|expr_list|statement SEMI_COLON")
    def parse_statement(self):
        '''Parsing statements and statement lists'''
        self.replace(2, "statement", self.peek(0).value)

    @rule(0, "statement statement !SEMI_COLON")
    def parse_combine_statements(self):
        stmt_list = Ast.ContainerNode(SrcPosition.invalid())

        stmt_list.append_child(self.peek(0).value)
        stmt_list.append_child(self.peek(1).value)
        self.replace(2, "statement_list", stmt_list)

    @rule(0, "statement_list statement|statement_list !SEMI_COLON")
    def parse_statement_list(self):
        stmt_list = self.peek(0).value

        stmt_list.append_children(self.peek(1).value)
        if self.blocks[-1][0] is not None:
            if self.check(2, "!CLOSE_CURLY"):
                self.start = self._cursor
            else:
                self.start = 0
        self.replace(2, "statement_list", stmt_list)

    @rule(0, "$struct expr statement")
    def parse_structs(self):
        struct = Ast.structs.StructDef(self.peek(0).pos, self.peek(1),
                                       self.peek(2).value, self.module)
        self.replace(3, "structdef", struct)

    @rule(0, "expr|paren DOT expr")
    def parse_member_access(self):
        op = Ast.math.ops['access_member'](self.peek(0).pos,
                                           self.peek(0).value,
                                           self.peek(2).value)
        self.replace(3, "expr", op)

    # * arrays
    @rule(0, "OPEN_SQUARE expr_list|expr CLOSE_SQUARE")
    def parse_array_literal_multi_element(self):
        '''check for all nodes dealing with arrays'''
        if self.check(-1, "CLOSE_SQUARE|expr|paren"):
            return
        if self.simple_check(-1, "KEYWORD") and \
                self.peek(-1).value not in self.keywords:
            return

        if self.peek(1).name == "expr":
            exprs = self.peek(1).value
        else:
            exprs = self.peek(1).value.children
        literal = Ast.ArrayLiteral(self.peek(0).pos, exprs)
        self.replace(3, "expr", literal)

    @rule(0, "OPEN_SQUARE expr SEMI_COLON expr CLOSE_SQUARE")
    def parse_array_literal(self):
        if self.check(-1, "CLOSE_SQUARE|expr"):
            return
        if self.simple_check(-1, "KEYWORD") and \
                self.peek(-1).value not in self.keywords:
            return
        amount = self.peek(3).value
        if not isinstance(amount, Ast.literals.numberliteral.Literal) or \
                self.peek(3).value.ret_type.name != "i32":
            errors.error("Array literal size must be an i32",
                         line=self.peek(3).pos)
        if amount.value <= 0:
            errors.error("Array literal size must be greater than '0'",
                         line=self.peek(3).pos)
        exprs = [self.peek(1).value] * amount.value
        literal = Ast.ArrayLiteral(self.peek(0).pos, exprs)
        self.replace(5, "expr", literal)

    @rule(0, "expr OPEN_SQUARE expr CLOSE_SQUARE")
    def parse_array_index(self):
        '''parse indexing of ararys'''
        expr = self.peek(2).value
        ref = self.peek(0).value
        fin = Ast.arrays.index.VariableIndexRef(self.peek(0).pos, ref, expr)
        self.replace(4, "expr", fin)

    @rule(0, "expr DOUBLE_DOT expr")
    def parse_rangelit(self):
        if self.peek_safe(3).name not in (*self.standard_expr_checks,
                                          *self.op_node_names):
            start = self.peek(0).value
            end = self.peek(2).value
            literal = Ast.literals.RangeLiteral(self.peek(0).pos, start, end)
            self.replace(3, "expr", literal)

    @rule(0, "$if expr statement !$else")
    def parse_if_statement(self):
        expr = self.peek(1).value
        block = self.peek(2).value
        x = Ast.flowcontrol.IfStatement(self.peek(0).pos, expr, block)
        self.replace(3, "statement", x)

    @rule(0, "$if expr statement $else statement")
    def parse_if_else(self):
        expr = self.peek(1).value
        block_if = self.peek(2).value
        block_else = self.peek(4).value
        x = Ast.flowcontrol.IfElseStatement(self.peek(0).pos, expr, block_if,
                                            block_else)
        self.replace(5, "statement", x)

    @rule(0, "$while expr statement")
    def parse_while_loop(self):
        expr = self.peek(1).value
        block = self.peek(2).value
        x = Ast.flowcontrol.WhileStatement(self.peek(0).pos, expr, block)
        self.replace(3, "statement", x)

    @rule(0, "$for expr $in expr statement")
    def parse_for_loop(self):
        if not isinstance(self.peek(1).value, Ast.variables.VariableRef):
            errors.error("'for loop' variable must be a variable name," +
                         " not an expression. ex:\nfor x in 0..12 {\n\n}",
                         line=self.peek(1).pos)
        expr = self.peek(1).value
        rang = self.peek(3).value
        block = self.peek(4).value
        x = Ast.flowcontrol.ForLoop(self.peek(0).pos, expr, rang, block)
        self.replace(5, "statement", x)

    @rule(0, "$continue SEMI_COLON")
    def parse_continue_stmt(self):
        x = Ast.flowcontrol.ContinueStatement(self.peek(0).pos)
        self.replace(2, "statement", x)

    @rule(0, "$break SEMI_COLON")
    def parse_break_stmt(self):
        x = Ast.flowcontrol.BreakStatement(self.peek(0).pos)
        self.replace(2, "statement", x)

    @rule(0, "$yield expr SEMI_COLON")
    def parse_yield_stmt(self):
        x = Ast.functions.YieldStatement(self.peek(0).pos, self.peek(1).value)
        self.replace(3, "statement", x)

    @rule(0, "KEYWORD KEYWORD expr|paren !RIGHT_ARROW")
    def parse_functions(self):
        '''Function definitions'''
        # * Function Definitions
        if self.check(0, '$define'):
            func_name = self.peek(1).value
            func = Ast.functions.definition.FunctionDef(self.peek(0).pos,
                                                        func_name,
                                                        self.peek(2).value,
                                                        None, self.module)
            # self.start_min = self._cursor
            self.replace(3, "func_def_portion", func)
        elif self.peek(0).value not in self.keywords:
            error(f"invalid syntax '{self.peek(0).value}'",
                  line=self.peek(0).pos)

    @rule(0, "KEYWORD KEYWORD expr|paren RIGHT_ARROW expr " +
             "OPEN_CURLY|SEMI_COLON")
    def parse_func_with_return(self):
        # * create function with return
        if self.check(0, '$define'):
            func_name = self.peek(1).value
            func = Ast.functions.definition.FunctionDef(self.peek(0).pos,
                                                        func_name,
                                                        self.peek(2).value,
                                                        None, self.module)
            func.ret_type = self.peek(4).value
            func.is_ret_set = True
            # self.start_min = self._cursor
            self.replace(5, "func_def_portion", func)
        elif self.peek(0).value not in self.keywords:
            error(f"invalid syntax '{self.peek(0).value}'",
                  line=self.peek(0).pos)

    @rule(0, "func_def_portion RIGHT_ARROW expr OPEN_CURLY|SEMI_COLON")
    def parse_func_double_return(self):
        # * bug check
        error(f"Function, '{self.peek(0).value.name}', " +
              "cannot have it's return-type set twice.", line=self.peek(1).pos)

    @rule(0, "func_def_portion statement")
    def parse_funcdef_with_body(self):
        # * complete function definition.
        self.peek(0).value.block = self.peek(1).value
        # self.start_min = self._cursor
        self.replace(2, "statement", self.peek(0).value)

    @rule(0, "func_def_portion SEMI_COLON")
    def parse_funcdef_empty(self):
        # self.start_min = self._cursor
        self.replace(2, "statement", self.peek(0).value)

    @rule(-1, "!DOT expr expr|paren")
    def parse_func_call(self):
        # * Function Calls
        func_name = self.peek(0).value
        args = self.peek(1).value

        if not isinstance(args, Ast.nodes.ParenthBlock):
            args = Ast.nodes.ParenthBlock(self.peek(1).pos)
            args.children.append(self.peek(1).value)

        func = Ast.functions.call.FunctionCall(self.peek(0).pos, func_name,
                                                args)
        self.replace(2, "expr", func)

    # @rule(0, "expr|paren DOT expr expr|paren")
    # def parse_func_call_dot(self):
    #     if not isinstance(self.peek(2).value, Ast.variables.VariableRef):
    #         return
    #     func_name = self.peek(2).value.var_name
    #     args1 = self.peek(0).value
    #     args2 = self.peek(3).value
    #     args1 = args1.children if isinstance(args1, Ast.nodes.ParenthBlock) \
    #         else [args1]  # wrap in a list if not already done
    #     args2 = args2.children if isinstance(args2, Ast.nodes.ParenthBlock) \
    #         else [args2]  # wrap in a list if not already done
    #     args = Ast.nodes.ParenthBlock(self.peek(0).pos)
    #     args.children = args1+args2
    #     func = Ast.functions.call.FunctionCall(self.peek(2).pos, func_name,
    #                                            args)
    #     self.replace(4, "expr", func)

    @rule(0, 'expr COLON expr COMMA|SEMI_COLON|CLOSE_PAREN|' +
             'CLOSE_CURLY|SET_VALUE')
    def parse_KV_pairs(self):
        '''check special rules'''
        if not isinstance(self.peek(0).value, Ast.variables.VariableRef):
            return

        kv = Ast.nodes.KeyValuePair(self.peek(0).pos, self.peek(0).value,
                                    self.peek(2).value)
        self.replace(3, "kv_pair", kv)

    # Does not use decorator.
    def parse_keyword_literals(self):
        '''literals like `true` and `false`, later `none`'''
        if self.check(0, '$true'):
            self.replace(1, "expr", Ast.literals.numberliteral.Literal(
                self.peek(0).pos, 1,
                Ast.Ast_Types.Type_Bool.Integer_1())
            )
        elif self.check(0, '$false'):
            self.replace(1, "expr", Ast.literals.numberliteral.Literal(
                self.peek(0).pos, 0,
                Ast.Ast_Types.Type_Bool.Integer_1())
            )
        elif self.check(0, '$PI'):
            self.replace(1, "expr", Ast.literals.numberliteral.Literal(
                self.peek(0).pos, 3.14159265358979323846,
                Ast.Ast_Types.Type_F32.Float_32())
            )
        elif self.check(0, '$TWO_PI'):
            self.replace(1, "expr", Ast.literals.numberliteral.Literal(
                self.peek(0).pos, 6.28318545718,
                Ast.Ast_Types.Type_F32.Float_32())
            )
        elif self.check(0, '$HALF_PI'):
            self.replace(1, "expr", Ast.literals.numberliteral.Literal(
                self.peek(0).pos, 1.57079632679489661923,
                Ast.Ast_Types.Type_F32.Float_32())
            )  # type: ignore
            # ^ Removing the previous comment some how kills the entire IDE

    @rule(0, "$return expr SEMI_COLON")
    def parse_return_statement(self):
        value = self.peek(1).value
        stmt = Ast.functions.returnstatement.ReturnStatement(self.peek(0).pos,
                                                             value)
        self.replace(3, 'statement', stmt)

    @rule(-1, "!COLON expr SET_VALUE expr|statement SEMI_COLON")
    def parse_var_decl(self):
        '''Parses variable declaration (without type annotation)'''
        # validate value
        if self.blocks[-1][0] is None:
            error("Variables cannot currently be defined in the global scope",
                  line=self.peek(0).pos)
        elif self.simple_check(2, "statement"):
            error("A variable's value cannot be set as a statement",
                  line=self.peek(0).pos)

        var_name = self.peek(0).value
        value = self.peek(2).value
        var = Ast.variables.VariableAssign(self.peek(0).pos, var_name, value,
                                           self.blocks[-1][0])
        self.replace(4, "statement", var)

    @rule(-1, "!$define KEYWORD")
    def parse_var_usage(self):
        if self.peek(0).value in self.keywords:
            return
        var = Ast.variables.VariableRef(self.peek(0).pos, self.peek(0).value,
                                        self.blocks[-1][0])
        self.replace(1, "expr", var)

    @rule(0, "AMP expr !OPEN_SQUARE")
    def parse_varref(self):
        var = self.peek(1).value
        typ = Ast.reference.Ref(self.peek(0).pos, var)
        self.replace(2, "expr", typ)
        # op = Ast.math.ops['ref'](self.peek(0).pos, self.peek(1).value,
        #                          Ast.nodes.ExpressionNode((-1,-1,-1)))
        # self.replace(2,"expr",op)

    @rule(0, "kv_pair SET_VALUE expr|statement SEMI_COLON")
    def parse_vardecl_explicit(self):
        '''variable declarations with explicit typing'''
        var_name = self.peek(0).value.key
        var_typ = self.peek(0).value.value
        if self.blocks[-1][0] is None:
            error("Variables cannot currently be defined outside of a block",
                  line=self.peek(0).pos)
        elif self.simple_check(2, "statement"):
            error("A variable's value cannot be set as a statement",
                  line=self.peek(0).pos)
        elif var_name in self.keywords:
            error("A variable's name cannot be a language keyword",
                  line=self.peek(0).pos)
        value = self.peek(2).value
        var = Ast.variables.VariableAssign(self.peek(0).pos, var_name,
                                           value, self.blocks[-1][0],
                                           typ=var_typ)
        self.replace(4, "statement", var)

    @rule(-1, '!expr SUB|SUM expr')
    def parse_numbers(self):
        '''Parse raw numbers into `expr` token.'''
        # * allow leading `+` or `-`.
        if isinstance(self.peek(1).value, Ast.Literal) and \
                self.peek(1).value.ret_type in (Ast.Ast_Types.Float_32(),
                                                Ast.Ast_Types.Integer_32()):
            if self.check(0, "SUB"):
                self.peek(1).value.value *= -1
                self.replace(2, "expr", self.peek(1).value)
            elif self.check(0, "SUM"):
                self.replace(2, "expr", self.peek(1).value)
        elif self.check(0, "SUB"):
            multiplier = Ast.literals.Literal(self.peek(0).pos, -1,
                                              Ast.Ast_Types.Integer_32())
            self.replace(2, "expr", Ast.math.ops["MUL"](self.peek(0).pos,
                                                        multiplier,
                                                        self.peek(1).value))

        elif self.check(0, "SUM"):
            self.replace(2, "expr", self.peek(1).value)

    def parse_math(self):
        '''Parse mathematical expressions'''
        if self.check_group_lookahead(0, '$not expr|paren') and \
                self.peek_safe(2).name != "DOUBLE_DOT":
            op = Ast.math.ops['not'](self.peek(0).pos, self.peek(1).value,
                                     Ast.nodes.ExpressionNode(
                                        SrcPosition.invalid()))
            self.replace(2, "expr", op)

        if self.peek_safe(3).name in self.standard_expr_checks:
            return
        # todo: add more operations
        # * Parse expressions
        if self.check_group(0, "expr|paren ISUM expr|paren SEMI_COLON"):
            op = Ast.math.ops["_ISUM"](self.peek(0).pos, self.peek(0).value,
                                       self.peek(2).value)
            self.replace(4, "statement", op)
        elif self.check_group(0, "expr|paren ISUB expr|paren SEMI_COLON"):
            op = Ast.math.ops["_ISUB"](self.peek(0).pos, self.peek(0).value,
                                       self.peek(2).value)
            self.replace(4, "statement", op)
        elif self.check_group(0, "expr|paren IMUL expr|paren SEMI_COLON"):
            op = Ast.math.ops["_IMUL"](self.peek(0).pos, self.peek(0).value,
                                       self.peek(2).value)
            self.replace(4, "statement", op)
        elif self.check_group(0, "expr|paren IDIV expr|paren SEMI_COLON"):
            op = Ast.math.ops["_IDIV"](self.peek(0).pos, self.peek(0).value,
                                       self.peek(2).value)
            self.replace(4, "statement", op)

        elif self.check_group(0, 'expr|paren _ expr|paren') and \
                self.peek(1).name in Ast.math.ops.keys():
            op_str = self.peek(1).name
            op = Ast.math.ops[op_str](self.peek(0).pos, self.peek(0).value,
                                      self.peek(2).value)
            self.replace(3, "expr", op)

        elif self.check_group(0, 'expr|paren $and expr|paren'):
            op = Ast.math.ops['and'](self.peek(0).pos, self.peek(0).value,
                                     self.peek(2).value)
            self.replace(3, "expr", op)

        elif self.check_group(0, 'expr|paren $or expr|paren'):
            op = Ast.math.ops['or'](self.peek(0).pos, self.peek(0).value,
                                    self.peek(2).value)
            self.replace(3, "expr", op)

        elif self.check_group(0, 'expr|paren $as expr|paren'):
            op = Ast.math.ops['as'](self.peek(0).pos, self.peek(0).value,
                                    self.peek(2).value)
            self.replace(3, "expr", op)

    @rule(0, "expr|expr_list|kv_pair|ELLIPSIS COMMA expr|kv_pair|ELLIPSIS")
    def parse_expr_list(self):
        # * parse expression lists
        if self.peek_safe(3).name in (*self.standard_expr_checks,
                                      *self.op_node_names):
            return

        expr = self.peek(0)
        out = None

        if expr.name == "expr_list":
            expr.value.append_children(self.peek(2).value)
            out = expr.value
        else:
            out = Ast.nodes.ParenthBlock(SrcPosition.invalid())
            out.append_child(expr.value)
            out.append_child(self.peek(2).value)

        if self.peek(0).name == "ELLIPSIS" or self.peek(2).name == "ELLIPSIS":
            out.contains_ellipsis = True

        self.replace(3, "expr_list", out)

    @rule(0, "OPEN_PAREN CLOSE_PAREN")
    def parse_paren_empty(self):
        '''Parses blocks of parenthises'''
        # * parse empty paren blocks
        node = Ast.ParenthBlock(self.peek(0).pos)
        node.set_end_pos(self.peek(1).pos)
        self.replace(2, "paren", node)
        self.parse_paren_close()

    @rule(0, "OPEN_PAREN")
    def parse_paren_start(self):
        # * parse paren start
        output = Ast.ParenthBlock(self.peek(0).pos)

        # * main implementation
        self.parens.append((output, self._cursor))

        self.start = self._cursor
        self._tokens[self._cursor] = \
            ParserToken("OPEN_PAREN_USED", '(', self._tokens[self._cursor].pos,
                        False)
        self.parse_paren_close()

    @rule(0, "OPEN_PAREN_USED expr|expr_list|kv_pair|ELLIPSIS CLOSE_PAREN")
    def parse_paren_close(self):
        # * parse full paren blocks
        name = "expr"

        paren = self.parens[-1][0]

        if self.simple_check(1, 'expr_list'):
            paren.children = self.peek(1).value.children
            paren.contains_ellipsis = self.peek(1).value.contains_ellipsis
            name = "paren"
        elif self.simple_check(1, 'expr') or self.simple_check(1, 'kv_pair'):
            paren.children = [self.peek(1).value]
        elif self.peek(1).name == "ELLIPSIS":
            paren.contains_ellipsis = True

        block = self.parens.pop()
        block[0].set_end_pos(self.peek(2).pos)

        self.start = self.parens[-1][1]

        self.replace(3, name, block[0])  # return to old block
