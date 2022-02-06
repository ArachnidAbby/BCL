import _AST,Errors

class parser_backend():
    def __init__(self,text,builder,module,printf):
        self._tokens  = text
        self._cursor  = 0
        self.builder  = builder
        self.module   = module
        self.printf   = printf
        self.program  = _AST.Program(builder,module)
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
            self._tokens.pop(index)
            #if index<self._cursor:
            #if self._cursor>0:
        self._cursor=max(self._cursor-amount+1,0)
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
    def parse(self,close_condition=lambda: False):
        self.functions={
            "println":_AST.Println
        }
        #print(dir(self._tokens[0]))
        while (not self.isEOF(self._cursor)) and (not close_condition()):
            #print(self._cursor,self._tokens)
            #print(self.peek(0))
            self.parse_math()
            self.parse_numbers()
            self.parse_parenth()
            self.parse_functions()
            
            self.move()
        #print(self._cursor,self._tokens)
        
        return self._tokens

    def parse_numbers(self,c=0):
        if self.check(c,"NUMBER"):
            self.insert(c+1,"num",_AST.Number(self.builder,self.module,int(self.peek(c)["value"])))
            self.consume(amount=1,index=c)

        elif not (self.check(c-1,'num') or self.check(c-1,'expr') or self.check(c-1,"parenth")):
            if self.check(c,"SUB"):
                if self.check(c+1,"NUMBER"):
                    self.insert(c+2,"num",_AST.Number(self.builder,self.module,-1*int(self.peek(c+1)["value"])))
                    self.consume(amount=2,index=c)
            elif self.check(c,"SUM"):
                if self.check(c+1,"NUMBER"):
                    self.insert(c+2,"num",_AST.Number(self.builder,self.module,int(self.peek(c+1)["value"])))
                    self.consume(amount=2,index=c)
    
    def parse_math(self,c=0):
        if self.check(c,"num") or self.check(c,'expr')or self.check(c,"parenth"):
            if self.check(c+1,"SUM"):
                if self.check(c+2,"num"):
                    self.insert(c+3,"expr",_AST.Sum(self.builder,self.module,self.peek(c)["value"],self.peek(c+2)["value"]))
                    self.consume(amount=3,index=c)
            elif self.check(c+1,"SUB"):
                if self.check(c+2,"num"):
                    self.insert(c+3,"expr",_AST.Sub(self.builder,self.module,self.peek(c)["value"],self.peek(c+2)["value"]))
                    self.consume(amount=3,index=c)
    
    def parse_parenth(self):
        if self.check(0,"OPEN_PAREN"):
            counter = 0
            l = _AST.Parenth()
            u = None
            closed=False
            cursor_origin = self._cursor
            pos = self.peek(0)["source_pos"].lineno
            self._cursor+=1
            #print("PEEKED ",self.peek(0))
            self.parse(close_condition=lambda: self.check(0,"CLOSE_PAREN"))
            self._cursor=cursor_origin-1
            counter=0
            while not self.isEOF(self._cursor+counter):
                if not u:
                    if self.check(counter,"expr")or self.check(counter,'num') or self.check(counter,'parenth'):
                        l.append(self.peek(counter)["value"])
                        u=True
                if self.check(counter,"COMMA"):
                    u=False
                if self.check(counter,"CLOSE_PAREN"):
                    closed = True
                    if u or u==None: break
                    else: Errors.Error.Unclosed_Parenth(pos)
                #self.move()
                    
                counter+=1
            if not closed: Errors.Error.Unclosed_Parenth(pos)
            self.insert(counter+1,"parenth", l)
            self.consume(amount=counter+1)
    
    def parse_functions(self):
        if self.check(0,"KEYWORD") and self.check(1,"parenth"):
            fname = self.peek(0)["value"]
            args  = self.peek(1)['value']
            z = self.functions[fname](self.program, self.printf,args,-1)
            self.insert(2,"func",z)
            self.consume(amount=2)
    
