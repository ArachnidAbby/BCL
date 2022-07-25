import Ast#,Errors

class parser_backend():
    def __init__(self,text, module, printf):
        self._tokens  = text
        self._cursor  = 0
        self.start = 0
        self.builder  = None
        self.module   = module
        self.printf   = printf
        # self.program  = Ast.Program(builder,module)
        self.doMove   = True
    
    #@property
    def isEOF(self,index=0):
        return index>=len(self._tokens)
    
    def move(self,index=1):
        if self.doMove:
            self._cursor+=index
        else:
            self.doMove=True

    def peek(self, index=0):
        index = self._cursor+index
        if self.isEOF(index=index):
            return None
        return self._tokens[index]
        
    def consume(self, index=0, amount=1):
        index = self._cursor+index
        if self.isEOF(index=index):
            return None
        
        for x in range(amount):
            # print(x)
            self._tokens.pop(index)
            #if index<self._cursor:
            #if self._cursor>0:
        # print(self._tokens)
        self._cursor= self.start #max(self._cursor-amount+1, self.start)
        #print(self._cursor)
        self.doMove=False
    
    def insert(self, index, name, value):
        self._tokens.insert(index+self._cursor,{"name":name,"value":value})
    
    def check(self, index, wanting):
        x = self.peek(index=index)
        if not x:
            return False
        return x["name"]==wanting

class parser(parser_backend):
    def __init__(self, *args, **kwargs):
        self.current_block = None
        super().__init__(*args, **kwargs)

    def parse(self, close_condition=lambda: False):
        self.start = self._cursor
        
        # self.functions={
        #     "println": Ast.Standard_Functions.Println
        # }
        #print(dir(self._tokens[0]))
        while (not self.isEOF(self._cursor)) and (not close_condition()):
            # print(self._cursor,self._tokens)
            # print()
            # print(self.peek(self.start-self._cursor))
            # print('\n')
            self.parse_blocks()
            self.parse_numbers()
            self.parse_math()
            self.parse_functions()
            self.parse_vars()
            # self.parse_parenth()
            
            self.move()
        #print(self._cursor,self._tokens)
        
        return self._tokens
    def parse_blocks(self, c=0):
        if not self.check(0, "OPEN_CURLY"):
            return None

        cursor_origin = self._cursor
        pos = self.peek(0)["source_pos"].lineno
        output = Ast.Block((-1,-1),"")

        old_block = self.current_block
        self.current_block = output
        old_start = self.start
        self.start = self._cursor+1

        self._cursor+=1
        self.parse(close_condition = lambda: self.check(0,"CLOSE_CURLY"))
        
        self._cursor=cursor_origin+1 # skip over '{'
        counter=0
        allow_next = True
        while (not self.isEOF(self._cursor+counter)) and (not self.check(counter, "CLOSE_CURLY")):
            print("PASTADA",self.peek(counter))
            if not self.check(counter,'SEMI_COLON') and allow_next:
                output.append_child(self.peek(counter)["value"])
                allow_next = False
            elif self.check(counter,'SEMI_COLON'):
                allow_next=True

            counter+=1
        
        self.insert(counter+1, "Block", output)
        self.start = old_start
        self.consume(amount=counter+2, index=-1)
        self.current_block = old_block
        
    
    def parse_functions(self):
        if self.check(0,"KEYWORD") and self.peek(0)["value"]=="define":
            if self.check(1,"KEYWORD") and self.check(2,"Block"):
                func_name = self.peek(1)["value"]
                block = self.peek(2)["value"]
                func = Ast.FunctionDef((-1,-1), '', None, func_name, block)
                self.insert(3,"func_def", func)
                self.consume(amount=3, index=0)
        
        # todo: add function calling
    
    def parse_vars(self):
        if self.check(0,"KEYWORD") and self.check(1,"SET_VALUE") and self.check(2,"expr") and self.check(3,"SEMI_COLON"):
            # validate value
            var_name = self.peek(0)["value"]
            value = self.peek(2)["value"]
            var = Ast.VariableAssign((-1,-1), '', None, var_name, value)
            self.current_block.variables[var_name] = None
            self.insert(3,"var_def", var)
            self.consume(amount=3, index=0)
        
        # reference known vars
        elif not self.check(1,"SET_VALUE"):
            if self.check(0,"KEYWORD") and self.current_block!=None and(self.peek(0)["value"] in self.current_block.variables.keys()):
                var = Ast.VariableRef((-1,-1), '', None, self.peek(0)["value"])
                self.insert(1,"expr", var)
                self.consume(amount=1, index=0)


    def parse_numbers(self):
        create_num = lambda x, m: Ast.Types.Number((-1,-1), "", None, m*int(self.peek(x)["value"]))
        if self.check(0,"NUMBER"):
            self.insert(1,"expr",create_num(0,1))
            self.consume(amount=1,index=0)

        elif not (self.check(-1,'num') or self.check(-1,'expr') or self.check(-1,"parenth")):
            if self.check(0,"SUB"):
                if self.check(1,"NUMBER"):
                    self.insert(2, "expr", create_num(1,-1))
                    self.consume(amount=2,index=0)
            elif self.check(0,"SUM"):
                if self.check(1,"NUMBER"):
                    self.insert(2, "expr", create_num(1,1))
                    self.consume(amount=2,index=0)
    
    def parse_math(self):
        if self.check(0,'expr'):
            if self.check(1,"SUM"):
                if self.check(2,"expr"):
                    self.insert(3,"expr",Ast.Sum((-1,-1),'',[self.peek(0)["value"],self.peek(2)["value"]]))
                    self.consume(amount=3,index=0)
            elif self.check(1,"SUB"):
                if self.check(2,"expr"):
                    self.insert(3,"expr",Ast.Sub(self.builder,self.module,[self.peek(0)["value"],self.peek(2)["value"]]))
                    self.consume(amount=3,index=0)
    
    # def parse_parenth(self):
    #     if self.check(0,"OPEN_PAREN"):
    #         counter = 0
    #         l = Ast.Parenth()
    #         u = None
    #         closed=False
    #         cursor_origin = self._cursor
    #         pos = self.peek(0)["source_pos"].lineno
    #         self._cursor+=1
    #         #print("PEEKED ",self.peek(0))
    #         self.parse(close_condition=lambda: self.check(0,"CLOSE_PAREN"))
    #         self._cursor=cursor_origin-1
    #         counter=0
    #         while not self.isEOF(self._cursor+counter):
    #             if not u:
    #                 if self.check(counter,"expr")or self.check(counter,'num') or self.check(counter,'parenth'):
    #                     l.append(self.peek(counter)["value"])
    #                     u=True
    #             if self.check(counter,"COMMA"):
    #                 u=False
    #             if self.check(counter,"CLOSE_PAREN"):
    #                 closed = True
    #                 if u or u==None: break
    #                 else: Errors.Error.Unclosed_Parenth(pos)
    #             #self.move()
                    
    #             counter+=1
    #         if not closed: Errors.Error.Unclosed_Parenth(pos)
    #         self.insert(counter+1,"parenth", l)
    #         self.consume(amount=counter+1)
    
    # def parse_functions(self):
    #     if self.check(0,"KEYWORD") and self.check(1,"parenth"):
    #         fname = self.peek(0)["value"]
    #         args  = self.peek(1)['value']
    #         z = self.functions[fname](self.program, self.printf,args,-1)
    #         self.insert(2,"func",z)
    #         self.consume(amount=2)
    
