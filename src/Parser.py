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

class parser(parser_backend):
    def __init__(self, *args, **kwargs):
        self.current_block = None
        # self.functions = dict

        super().__init__(*args, **kwargs)

    def parse(self, close_condition: Callable[[],bool]=lambda: False):
        '''Parser main'''

        previous_start_position = self.start
        self.start = self._cursor   # where to reset cursor after consuming tokens.
        
        # * to be reimplemented in the next commits
        # self.functions={
        #     "println": Ast.Standard_Functions.Println
        # }

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
            self.parse_vars()
            self.parse_parenth() # * to be reimplemented in the next commits
            
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
        if self.check(0,"KEYWORD") and self.peek(0)["value"]=="define":
            if self.check(1,"KEYWORD") and self.check(2,"Block"):
                func_name = self.peek(1)["value"]
                block = self.peek(2)["value"]
                func = Ast.FunctionDef((-1,-1), '', None, func_name, block, self.module)
                # self.functions[func_name] = func
                self.insert(3,"func_def", func)
                self.consume(amount=3, index=0)
        
        # todo: add function calling. Make sure this inserts an `expr` node
        elif self.check(0,"KEYWORD") and (self.check(1, "expr") or self.check(1, "paren")):
            # if self.peek(0)["value"] in Ast.Function.functions.keys():
            func_name = self.peek(0)["value"]
            args = self.peek(1)["value"]
            func = Ast.FunctionCall(self.peek(0)["source_pos"], func_name, None, func_name, args)
            self.insert(2,"expr", func)
            self.consume(amount=2, index=0)
    
    def parse_vars(self):
        '''Parses everything involving Variables. References, Instantiation, value changes, etc.'''

        # * Variable Assignment
        if self.check(0,"KEYWORD") and self.check(1,"SET_VALUE") and self.check(2,"expr") and self.check(3,"SEMI_COLON"):
            # validate value
            var_name = self.peek(0)["value"]
            value = self.peek(2)["value"]
            var = Ast.VariableAssign((-1,-1), '', None, var_name, value, self.current_block)
            self.insert(3,"var_def", var)
            self.consume(amount=3, index=0)
        
        # * Variable References
        elif not self.check(1,"SET_VALUE"):
            if self.check(0,"KEYWORD") and self.current_block!=None and(self.peek(0)["value"] in self.current_block.variables.keys()):
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
        elif not self.check(-1,'expr'):
            if self.check(0,"SUB"):
                if self.check(1,"NUMBER"):
                    self.insert(2, "expr", create_num(1,-1))
                    self.consume(amount=2,index=0)
            elif self.check(0,"SUM"):
                if self.check(1,"NUMBER"):
                    self.insert(2, "expr", create_num(1,1))
                    self.consume(amount=2,index=0)
    
    def parse_math(self):
        '''Parse mathematical expressions'''

        # todo: add more operations

        # * Parse expressions
        if self.check(0,'expr') and self.check(2,"expr"):
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
            if not self.check(counter,'COMMA') and allow_next:
                output.append_child(self.peek(counter)["value"])
                allow_next = False
            elif self.check(counter,'COMMA'):
                if allow_next: error.error("Syntax error: ',,'")
                allow_next=True
            elif not allow_next:
                error.error("Syntax error: missing ','")


            counter+=1
        name = "paren" if counter>1 else "expr"
        # print(name)
        # print(output.ret_type)
        self.insert(counter+1, name, output)
        self.consume(amount=counter+2, index=-1)