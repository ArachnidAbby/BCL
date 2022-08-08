from typing import Callable

import Ast
from Parser_Base import ParserBase
from Errors import error


class parser(ParserBase):
    def __init__(self, *args, **kwargs):
        self.current_block = None
        self.statements = [
            'return'
        ]
        self.keywords = [
            "define", "return"
        ]

        self.simple_rules = [
            ("statement", "$return expr SEMI_COLON", Ast.Function.ReturnStatement, (1,) )
        ]

        super().__init__(*args, **kwargs)
    
    def parse_once(self):
        self.parse_blocks()
        self.parse_numbers()
        self.parse_math()
        self.parse_functions()
        self.parse_special()
        self.parse_vars()
        self.parse_parenth()

        # * parse the most basic rules possible
        for rule in self.simple_rules:
            if self.check_group(0,rule[1]):
                rule_len = len(rule[1].split(' '))
                start_token = self.peek(0)
                args = [self.peek(x)["value"] for x in rule[3]]
                out = rule[2](start_token["source_pos"], None, *args)
                self.insert(rule_len, rule[0], out)
                self.consume(amount=rule_len)

    def parse(self, close_condition: Callable[[],bool]=lambda: False):
        '''Parser main'''

        previous_start_position = self.start
        self.start = self._cursor   # where to reset cursor after consuming tokens.

        while (not self.isEOF(self._cursor)) and (not close_condition()):

            # * code for debugging. Use if needed
            # print(self._cursor,self._tokens)
            # print()
            # print(self.peek(self.start-self._cursor))
            # print('\n')
            # * end of debug code

            self.parse_once()
            self.move_cursor()
        
        self.start = previous_start_position

        return self._tokens

    def parse_blocks(self):
        '''Parses blocks of Curly-braces'''

        # * gaurd clause
        if not self.check(0, "OPEN_CURLY"):
            return None

        # * check for function declaration before the block.
        # * this lets arguments be interpreted as usable variables.
        output = Ast.Block(self.peek(0)["source_pos"])
        if self.check(-1,"func_def_portion"):
            for x in self.peek(-1)["value"].args.keys():
                output.variables[x] = self.peek(-1)["value"].args[x]

        # * main implementation
        old_block = self.current_block # save the old block in the case of nested blocks.
        self.current_block = output
        
        o, counter = self.delimited("SEMI_COLON", "CLOSE_CURLY")
        output.children = o

        self.insert(counter+1, "Block", output)
        self.consume(amount=counter+2, index=-1)
        self.current_block = old_block # return to old block
        
    
    def parse_functions(self):
        '''Everything involving functions. Calling, definitions, etc.'''

        # * Function Definitions
        if self.check_group(0,"KEYWORD KEYWORD expr|paren"):
            if self.peek(0)['value'] == 'define':
                func_name = self.peek(1)["value"]
                block = self.peek(2)["value"]
                func = Ast.FunctionDef(self.peek(0)["source_pos"], None, func_name, self.peek(2)["value"], block, self.module)
                self.insert(3,"func_def_portion", func)
                self.consume(amount=3, index=0)
            else:
                error(f"invalid syntax '{self.peek(0)['value']}'", line = self.peek(0)["source_pos"])
        
        # * Set Function Return Type 
        elif self.check_group(0,"func_def_portion RIGHT_ARROW KEYWORD"):
            if self.peek(0)["value"].is_ret_set:
                error(f"Function, \"{self.peek(0)['value'].name}\", cannot have it's return-type set twice.", line = self.peek(0)["source_pos"])
            self.peek(0)["value"].ret_type = self.peek(2)["value"]
            self.peek(0)["value"].is_ret_set = True
            self.insert(3,"func_def_portion", self.peek(0)["value"], completed = False)
            self.consume(amount=3, index=0)

        # * complete function definition.
        elif self.check_group(0,"func_def_portion Block"):
            self.peek(0)["value"].block = self.peek(1)["value"]
            self.insert(2,"func_def", self.peek(0)["value"])
            self.consume(amount=2, index=0)
        
        # * Function Calls
        elif self.check_group(0,"KEYWORD expr|paren") and (self.peek(0)["value"] not in self.statements):
            func_name = self.peek(0)["value"]
            args = self.peek(1)["value"]
            func = Ast.FunctionCall(self.peek(0)["source_pos"], None, func_name, args)
            self.insert(2,"expr", func)
            self.consume(amount=2, index=0)

        # * different func calls "9.to_string()" as an example
        elif self.check_group(0,"expr|paren DOT KEYWORD expr|paren") and (self.peek(2)["value"] not in self.statements):
            func_name = self.peek(2)["value"]
            args1 = self.peek(0)["value"]
            args2 = self.peek(3)["value"]
            args1 = args1.children if isinstance(args1, Ast.Nodes.ParenthBlock) else [args1]
            args2 = args2.children if isinstance(args2, Ast.Nodes.ParenthBlock) else [args2]
            args = Ast.Nodes.ParenthBlock(self.peek(0)["source_pos"], args1+args2)
            func = Ast.FunctionCall(self.peek(2)["source_pos"], None, func_name, args)
            self.insert(4,"expr", func)
            self.consume(amount=4, index=0)
    
    def parse_special(self):
        '''check special rules'''

        # * KV pairs
        if self.check_group(0, '_ COLON _'):
            keywords = self.check_group(0, 'KEYWORD COLON KEYWORD')
                # error(f"A Key-Value pair cannot be created for token {self.peek(0)['name']}", line = self.peek(0)["source_pos"])
            kv = Ast.Nodes.KeyValuePair(self.peek(0)["source_pos"], None, self.peek(0)["value"], self.peek(2)["value"], keywords = keywords)
            self.insert(3,"kv_pair", kv)
            self.consume(amount=3, index=0)
    
    def parse_vars(self):
        '''Parses everything involving Variables. References, Instantiation, value changes, etc.'''

        # * Variable Assignment
        if self.check_group(0,"KEYWORD SET_VALUE expr|statement SEMI_COLON"):
            # validate value
            if self.current_block == None:
                error("Variables cannot currently be defined outside of a block", line = self.peek(0)["source_pos"])
            elif self.check(2, "statement"):
                error("A variables value cannot be set as a statement", line = self.peek(0)["source_pos"])
            var_name = self.peek(0)["value"]
            value = self.peek(2)["value"]
            var = Ast.VariableAssign(self.peek(0)["source_pos"], None, var_name, value, self.current_block)
            self.insert(3,"statement", var)
            self.consume(amount=3, index=0)
        
        # * Variable References
        elif self.current_block!=None and self.check_group(0,"KEYWORD !SET_VALUE"):
            if self.peek(0)["value"] in self.current_block.variables.keys():
                var = Ast.VariableRef(self.peek(0)["source_pos"], None, self.peek(0)["value"], self.current_block)
                self.insert(1,"expr", var)
                self.consume(amount=1, index=0)


    def parse_numbers(self):
        '''Parse raw integers into `expr` token.'''

        create_num = lambda x, m: Ast.Types.Integer_32(self.peek(0)["source_pos"], None, m*int(self.peek(x)["value"]))
        
        # * Turn `NUMBER` token into an expr
        if self.check(0,"NUMBER"):
            self.insert(1,"expr",create_num(0,1))
            self.consume(amount=1,index=0)

        # * allow leading `+` or `-`.
        elif self.check_group(-1,'!expr SUB|SUM NUMBER'):
            if self.check(0,"SUB"):
                self.insert(2, "expr", create_num(1,-1))
                self.consume(amount=2,index=0)
            elif self.check(0,"SUM"):
                self.insert(2, "expr", create_num(1,1))
                self.consume(amount=2,index=0)
    
    def parse_math(self):
        '''Parse mathematical expressions'''

        # todo: add more operations

        # * Parse expressions
        if self.check_group(0,'expr _ expr') and self.peek(1)['name'] in Ast.Math.ops.keys():
            op_str =self.peek(1)['name']
            op = Ast.Math.ops[op_str](self.peek(0)["source_pos"],[self.peek(0)["value"],self.peek(2)["value"]])
            self.insert(3,"expr",op)
            self.consume(amount=3,index=0)
    
    def parse_parenth(self):
        '''Parses blocks of parenthises'''

        # * gaurd clause
        if not self.check(0, "OPEN_PAREN"):
            return None

        # * main implementation
        peek = self.peek(0)
        pos = peek["source_pos"]
        output = Ast.ParenthBlock(pos)

        o, counter = self.delimited("COMMA", "CLOSE_PAREN")
        output.children = o

        name = "paren" if counter>1 else "expr"

        self.insert(counter+1, name, output)
        self.consume(amount=counter+2, index=-1)