from typing import Callable

import Ast
from Errors import error  # ,Errors


class parser_backend():
    '''Backend of the Parser.
        This is primarily to seperate the basics of parsing from the actual parse for the language.
    '''

    def __init__(self, text, module):
        self._tokens  = text
        self._cursor  = 0
        self.start    = 0
        self.builder  = None
        self.module   = module
        self.doMove   = True
    
    def isEOF(self, index: int=0) -> bool:
        '''Checks if the End-Of-File has been reached'''
        return index>=len(self._tokens)
    
    def move(self,index: int=1):
        '''Moves the cursor unless `!self.doMove` '''
        if self.doMove:
            self._cursor+=index
        else:
            self.doMove=True

    def peek(self, index: int) -> dict:
        '''peek into the token list and fetch a token'''
        index = self._cursor+index
        if self.isEOF(index=index):
            return {"name":"EOF","value":''}
        return self._tokens[index]
    
    # todo: make this just use positional arguments for the amount.
    def consume(self, index: int=0, amount: int=1):
        '''Consume a specific `amount` of tokens starting at `index`'''
        index = self._cursor+index
        if self.isEOF(index=index):
            return None
        
        for x in range(amount):
            self._tokens.pop(index)

        self._cursor= self.start 
        self.doMove=False
    
    def insert(self, index: int, name: str, value: Ast.Nodes.AST_NODE):
        '''insert tokens at a specific location'''
        self._tokens.insert(index+self._cursor,{"name":name,"value":value})
    
    def check(self, index: int, wanting: str) -> bool:
        '''check the value of a token'''
        x = self.peek(index=index)
        if not x:
            return False
        return x["name"]==wanting

    def check_group(self, start_index: int, wanting: str) -> bool:
        '''check a group  of tokens in the format 'token1 token2 token3|token3alt ...' '''
        tokens = wanting.split(' ')
        output = []

        for c,x in enumerate(tokens):
            if x == '_': # skip tokens/allow any
                continue
            elif '|' in x: # `or` operation
                output.append(any([self.check(c+start_index,y) for y in x.split('|')]))
            elif x.startswith('!'): # `not` operation
                output.append(not self.check(c+start_index,x[1:]))
            elif x.startswith('$'): # `match value` operation
                output.append(self.peek(c+start_index)["value"]==x[1:])
            else:
                output.append(self.check(c+start_index,x))

        return all(output)


class parser(parser_backend):
    def __init__(self, *args, **kwargs):
        self.current_block = None
        self.statements = [
            'return'
        ]
        self.keywords = [
            "define"
        ]

        super().__init__(*args, **kwargs)

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

            self.parse_blocks()
            self.parse_numbers()
            self.parse_math()
            self.parse_functions()
            self.parse_special()
            self.parse_vars()
            self.parse_parenth()
            
            self.move()
        
        self.start = previous_start_position

        return self._tokens

    def parse_blocks(self):
        '''Parses blocks of Curly-braces'''

        # * gaurd clause
        if not self.check(0, "OPEN_CURLY"):
            return None

        # * main implementation
        output = Ast.Block((-1,-1),"")
        if self.check(-1,"func_def_portion"):
            for x in self.peek(-1)["value"].args.keys():
                output.variables[x] = self.peek(-1)["value"].args[x]

        self._cursor+=1 # skip over '{'
        cursor_origin = self._cursor
        old_block = self.current_block # save the old block in the case of nested blocks.
        self.current_block = output

        self.parse(close_condition = lambda: self.check(0,"CLOSE_CURLY"))
        
        self._cursor=cursor_origin # set cursor back to origin after the `parse()`

        
        # * add statements to the block until a `CLOSE_CURLY` token is reached.
        counter=0       # stores a mini cursor and stores the total amount of tokens to consume at the end.
        allow_next = True       # allow another statement in the block

        while (not self.isEOF(self._cursor+counter)) and (not self.check(counter, "CLOSE_CURLY")):
            if not self.check(counter,'SEMI_COLON') and allow_next:
                output.append_child(self.peek(counter)["value"])
                allow_next = False
            elif self.check(counter,'SEMI_COLON'):
                allow_next=True

            counter+=1
        
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
                func = Ast.FunctionDef((-1,-1), '', None, func_name, self.peek(2)["value"], block, self.module)
                self.insert(3,"func_def_portion", func)
                self.consume(amount=3, index=0)
            else:
                error(f"invalid syntax '{self.peek(0)['value']}'")
        
        # * Set Function Return Type 
        elif self.check_group(0,"func_def_portion RIGHT_ARROW KEYWORD"):
            if self.peek(0)["value"].is_ret_set:
                error(f"Function {self.peek(0)['value'].name}'s cannot have it's return set twice.")
            self.peek(0)["value"].ret_type = self.peek(2)["value"]
            self.peek(0)["value"].is_ret_set = True
            self.insert(3,"func_def_portion", self.peek(0)["value"])
            self.consume(amount=3, index=0)
        
        # * Return statement
        elif self.check_group(0, "$return expr SEMI_COLON"):
            x = Ast.Function.ReturnStatement((-1,-1), '', None, self.peek(1)["value"])
            self.insert(2,"statement", x)
            self.consume(amount=2, index=0)

        # * complete function definition.
        elif self.check_group(0,"func_def_portion Block"):
            self.peek(0)["value"].block = self.peek(1)["value"]
            self.insert(2,"func_def", self.peek(0)["value"])
            self.consume(amount=2, index=0)
        
        # * Function Calls
        elif self.check_group(0,"KEYWORD expr|paren") and (self.peek(0)["value"] not in self.statements):
            func_name = self.peek(0)["value"]
            args = self.peek(1)["value"]
            func = Ast.FunctionCall(self.peek(0)["source_pos"], func_name, None, func_name, args)
            self.insert(2,"expr", func)
            self.consume(amount=2, index=0)

        # * different func calls "9.to_string()" as an example
        elif self.check_group(0,"expr|paren DOT KEYWORD expr|paren") and (self.peek(2)["value"] not in self.statements):
            func_name = self.peek(2)["value"]
            args1 = self.peek(0)["value"]
            args2 = self.peek(3)["value"]
            args1 = args1.children if isinstance(args1, Ast.Nodes.ParenthBlock) else [args1]
            args2 = args2.children if isinstance(args2, Ast.Nodes.ParenthBlock) else [args2]
            args = Ast.Nodes.ParenthBlock((-1,-1), '', args1+args2)
            func = Ast.FunctionCall(self.peek(2)["source_pos"], func_name, None, func_name, args)
            self.insert(4,"expr", func)
            self.consume(amount=4, index=0)
    
    def parse_special(self):
        '''check special rules'''

        # * KV pairs
        if self.check_group(0, '_ COLON _'):
            kv = Ast.Nodes.KeyValuePair((-1,-1), '', None, self.peek(0)["value"], self.peek(2)["value"])
            self.insert(3,"kv_pair", kv)
            self.consume(amount=3, index=0)
    
    def parse_vars(self):
        '''Parses everything involving Variables. References, Instantiation, value changes, etc.'''

        # * Variable Assignment
        if self.check_group(0,"KEYWORD SET_VALUE expr SEMI_COLON"):
            # validate value
            var_name = self.peek(0)["value"]
            value = self.peek(2)["value"]
            var = Ast.VariableAssign((-1,-1), '', None, var_name, value, self.current_block)
            self.insert(3,"statement", var)
            self.consume(amount=3, index=0)
        
        # * Variable References
        elif self.current_block!=None and self.check_group(0,"KEYWORD !SET_VALUE"):
            if self.peek(0)["value"] in self.current_block.variables.keys():
                var = Ast.VariableRef((-1,-1), '', None, self.peek(0)["value"], self.current_block)
                self.insert(1,"expr", var)
                self.consume(amount=1, index=0)


    def parse_numbers(self):
        '''Parse raw integers into `expr` token.'''

        create_num = lambda x, m: Ast.Types.Integer_32((-1,-1), "", None, m*int(self.peek(x)["value"]))
        
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
        if self.check_group(0,'expr _ expr'):
            if self.check(1,"SUM"):
                self.insert(3,"expr",Ast.Sum((-1,-1),'',[self.peek(0)["value"],self.peek(2)["value"]]))
                self.consume(amount=3,index=0)
            elif self.check(1,"SUB"):
                self.insert(3,"expr",Ast.Sub((-1,-1),'',[self.peek(0)["value"],self.peek(2)["value"]]))
                self.consume(amount=3,index=0)
            elif self.check(1,"MUL"):
                self.insert(3,"expr",Ast.Mul((-1,-1),'',[self.peek(0)["value"],self.peek(2)["value"]]))
                self.consume(amount=3,index=0)
            elif self.check(1,"DIV"):
                self.insert(3,"expr",Ast.Div((-1,-1),'',[self.peek(0)["value"],self.peek(2)["value"]]))
                self.consume(amount=3,index=0)
            elif self.check(1,"MOD"):
                self.insert(3,"expr",Ast.Mod((-1,-1),'',[self.peek(0)["value"],self.peek(2)["value"]]))
                self.consume(amount=3,index=0)
            elif self.check(1,"EQ"):
                self.insert(3,"expr",Ast.Eq((-1,-1),'',[self.peek(0)["value"],self.peek(2)["value"]]))
                self.consume(amount=3,index=0)
    
    def parse_parenth(self):
        '''Parses blocks of parenthises'''

        # * gaurd clause
        if not self.check(0, "OPEN_PAREN"):
            return None

        # * main implementation
        peek = self.peek(0)
        pos = peek["source_pos"]
        output = Ast.ParenthBlock(pos,peek["value"])

        self._cursor+=1 # skip over '{'
        cursor_origin = self._cursor

        self.parse(close_condition = lambda: self.check(0,"CLOSE_PAREN"))
        
        self._cursor=cursor_origin # set cursor back to origin after the `parse()`

        
        # * add statements to the block until a `CLOSE_CURLY` token is reached.
        counter=0       # stores a mini cursor and stores the total amount of tokens to consume at the end.
        allow_next = True       # allow another statement in the block

        while (not self.isEOF(self._cursor+counter)) and (not self.check(counter, "CLOSE_PAREN")):
            if (not self.check(counter,'COMMA')) and allow_next:
                output.append_child(self.peek(counter)["value"])
                allow_next = False
            elif self.check(counter,'COMMA'):
                if allow_next: error.error("Syntax error: ',,'")
                allow_next=True
            elif not allow_next:
                error.error("Syntax error: missing ','")


            counter+=1
        name = "paren" if counter>1 else "expr"
        
        self.insert(counter+1, name, output)
        self.consume(amount=counter+2, index=-1)