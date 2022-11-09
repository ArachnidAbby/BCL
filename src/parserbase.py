from typing import Any, Callable, NamedTuple

import Ast
from errors import error


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
    __slots__ = ('_tokens', '_cursor', 'start', 'builder', 'module', 'do_move', 'start_min')
    '''Backend of the Parser.
        This is primarily to seperate the basics of parsing from the actual parse for the language.
    '''

    def __init__(self, text, module):
        self._tokens  = text
        self._cursor  = 0
        self.start    = 0
        self.module   = module
        self.do_move   = True
        self.start_min = 0
    
    
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

        self._cursor= max(self.start, self.start_min)
        self.do_move=False
    
    
    def insert(self, index: int, name: str, value: Ast.nodes.ASTNode, completed = True):
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

    def simple_check(self, index: int, wanting: str) -> bool:
        '''check the value of a token (without formatting)'''
        return self.peek(index=index).name==wanting
    
    def replace(self, leng: int, name: str, value, i: int = 0, completed: bool = True):
        '''replace a group of tokens with a single token.'''
        self._consume(amount=leng, index=-i)
        self.insert(i, name, value, completed = completed)

        self._cursor= max(self.start, self.start_min)
        self.do_move=False
        

    def check_group(self, start_index: int, wanting: str) -> bool:
        '''check a group of tokens in a string seperated by spaces.'''
        tokens = wanting.split(' ')

        if (len(tokens)+self._cursor+start_index) > len(self._tokens):
            return False

        for c,x in enumerate(tokens):
            if not self.check(c+start_index,x):
                return False
                
        return True

    def check_simple_group(self, start_index: int, wanting: str) -> bool:
        '''check a group of tokens in a string seperated by spaces. (unformatted)'''
        tokens = wanting.split(' ')

        if (len(tokens)+self._cursor+start_index) > len(self._tokens):
            return False

        for c,x in enumerate(tokens):
            if not self.simple_check(c+start_index,x):
                return False

        return True

    def match_multiple(self, start: int):
        end = self._cursor
        end_node = self.peek(0)
        self._cursor = start+1
        
        while not self.isEOF() and self._tokens[self._cursor]!=end_node:
            yield
            self.move_cursor()

        self._cursor = start
        
        


