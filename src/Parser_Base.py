from typing import Callable

import Ast
from Errors import error


class ParserBase():
    __slots__ = ['_tokens', '_cursor', 'start', 'builder', 'module', 'do_move']
    '''Backend of the Parser.
        This is primarily to seperate the basics of parsing from the actual parse for the language.
    '''

    def __init__(self, text, module):
        self._tokens  = text
        self._cursor  = 0
        self.start    = 0
        self.module   = module
        self.do_move   = True
    
    def isEOF(self, index: int=0) -> bool:
        '''Checks if the End-Of-File has been reached'''
        return index>=len(self._tokens)
    
    def move_cursor(self,index: int=1):
        '''Moves the cursor unless `!self.doMove` '''
        if self.do_move:
            self._cursor+=index
        else:
            self.do_move=True

    def peek(self, index: int) -> dict:
        '''peek into the token list and fetch a token'''
        index = self._cursor+index
        if self.isEOF(index=index):
            return {"name":"EOF","value":'', 'completed': False}
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
        self.do_move=False
    
    def insert(self, index: int, name: str, value: Ast.Nodes.AST_NODE, completed = True):
        '''insert tokens at a specific location'''
        self._tokens.insert(index+self._cursor,{"name":name,"value":value,"completed":completed, "source_pos": value.position})
    
    def check(self, index: int, wanting: str) -> bool:
        '''check the value of a token (with formatting)'''
        x = self.peek(index=index)
        if not x:
            return False

        if wanting == '_': # allow any
            return True
        elif wanting == '__': # allow any with "complete" == True
            return x["completed"]
        elif wanting == '_!_': # allow any with "complete" == False
            return not x["completed"]
        elif wanting.startswith('!'): # `not` operation
            return not self.check(index, wanting[1:])
        elif wanting.startswith('$'): # `match value` operation
            return x["value"]==wanting[1:]
        elif '|' in wanting: # `or` operation
            return any([self.check(index,y) for y in wanting.split('|')])
        else:
            return x["name"]==wanting



    def check_group(self, start_index: int, wanting: str) -> bool:
        '''check a group  of tokens in a string seperated by spaces.'''
        tokens = wanting.split(' ')

        return all([self.check(c+start_index,x) for c,x in enumerate(tokens)])

    def delimited(self, sep: str, end: str, allow_statements = True) -> tuple[list, int]:
        '''parse "lists" of tokens like in parenthesis or a curly block'''
        
        output=[]
        self._cursor+=1 # skip over start
        cursor_origin = self._cursor # save old origin point
        ln = self.peek(-1)["source_pos"]
        self.parse(close_condition = lambda: self.check(0, end))
        self._cursor=cursor_origin # set cursor back to origin after the `parse()`

        counter=0       # stores a mini cursor and stores the total amount of tokens to consume at the end.
        allow_next = True       # allow another Node in the block
        while not self.check(counter, end):
            if self.check(counter, '__'):
                if allow_next: 
                    output.append(self.peek(counter)["value"])
                else:
                    error(f"missing '{sep}'", line = self.peek(counter)["source_pos"])
                allow_next = allow_statements and self.check(counter,'statement')
            elif self.check(counter, sep):
                allow_next=True
            elif self.isEOF(self._cursor+counter):
                error(f"EOF reached before {end} closed.", line = ln)
            counter+=1

        return output, counter
    
    def parse(self, close_condition: Callable[[],bool]=lambda: False):
        pass
