from typing import Any, Callable, NamedTuple

import Ast
from Errors import error


class ParserToken(NamedTuple):
    # __slots__ = ('name', 'value', 'source_pos', 'completed')

    name: str
    value: Any
    source_pos: tuple[int, int, int]
    completed: bool

    @property
    def pos(self):
        return self.source_pos
        
class ParserBase:
    __slots__ = ('_tokens', '_cursor', 'start', 'builder', 'module', 'do_move')
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
        
        self._cursor += index if self.do_move else 0
        self.do_move  = True

    def peek(self, index: int) -> ParserToken:
        '''peek into the token list and fetch a token'''
        return self._tokens[self._cursor+index]
    
    def _consume(self, index: int=0, amount: int=1):
        '''consume specific amount of tokens but don't reset cursor position'''
        index = self._cursor+index

        del self._tokens[index : index+amount]

    # todo: make this just use positional arguments for the amount.
    def consume(self, index: int=0, amount: int=1):
        '''Consume a specific `amount` of tokens starting at `index`'''
        self._consume(index = index, amount = amount)

        self._cursor= self.start 
        self.do_move=False
    
    def insert(self, index: int, name: str, value: Ast.Nodes.AST_NODE, completed = True):
        '''insert tokens at a specific location'''
        self._tokens.insert(index+self._cursor, ParserToken(name, value, value.position, completed))
    
    def check(self, index: int, wanting: str) -> bool:
        '''check the value of a token (with formatting)'''
        x = self.peek(index=index)

        if wanting == '_': # allow any
            return True
        elif wanting == '__': # allow any with "complete" == True
            return x.completed
        elif wanting.startswith('!'): # `not` operation
            return not self.check(index, wanting[1:])
        elif wanting.startswith('$'): # `match value` operation
            return x.value==wanting[1:]
        elif '|' in wanting: # `or` operation
            for y in wanting.split('|'):
                if self.check(index,y): return True
            return False
        else:
            return x.name==wanting

    def replace(self, l: int, name: str, value, i: int = 0, completed: bool = True):
        '''replace a group of tokens with a single token.'''
        self._consume(amount=l, index=-i)
        self.insert(i, name, value, completed = completed)

        self._cursor= self.start 
        self.do_move=False
        

    def check_group(self, start_index: int, wanting: str) -> bool:
        '''check a group of tokens in a string seperated by spaces.'''
        tokens = wanting.split(' ')

        if (len(tokens)+self._cursor+start_index-1) > len(self._tokens):
            return False

        for c,x in enumerate(tokens):
            if not self.check(c+start_index,x):
                return False

        return True

    def delimited(self, sep: str, end: str, allow_statements = True) -> tuple[list, int]:
        '''parse "lists" of tokens like in parenthesis or a curly block'''
        
        output=[]
        self._cursor+=1 # skip over start
        cursor_origin = self._cursor # save old origin point
        ln = self.peek(-1).pos
        self.parse(close_condition = lambda: self.check(0, end))
        self._cursor=cursor_origin # set cursor back to origin after the `parse()`

        counter=0       # stores a mini cursor and stores the total amount of tokens to consume at the end.
        allow_next = True       # allow another Node in the block
        while not self.check(counter, end):
            if self.check(counter, '__'):
                if allow_next: 
                    output.append(self.peek(counter).value)
                else:
                    error(f"missing '{sep}'", line = self.peek(counter).pos)
                allow_next = allow_statements and self.check(counter,'statement')
            elif self.check(counter, sep):
                allow_next=True
            elif self.check(counter, '!__'):
                sym = self.peek(counter)
                error(f"unknown symbol '{sym.value}'", line = sym.pos)
            elif self.isEOF(self._cursor+counter):
                error(f"EOF reached before {end} closed.", line = ln)
            counter+=1

        return output, counter
    
    def parse(self, close_condition: Callable[[],bool]=lambda: False):
        pass
