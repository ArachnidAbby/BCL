from typing import Any, Callable, NamedTuple

import Ast
import errors


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
    __slots__ = ('_tokens', '_cursor', 'start', 'builder', 'module', 'do_move', 'start_min', 'parsing_functions')
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
        self.parsing_functions = {}
    
    def parse(self, close_condition: Callable[[],bool]=lambda: False):
        '''Parser main'''
        previous_start_position = self.start
        self.start = self._cursor   # where to reset cursor after consuming tokens.
        iters = 0
        while (not self.isEOF(self._cursor)): # and (not close_condition()):
            # * code for debugging. Use if needed
            # print(self._cursor)
            # print(',\n'.join([f'{x.name}||{x.value}' for x in self._tokens]))
            # print()
            # * end of debug code
            token_name = self.peek(0).name
            if token_name not in self.parsing_functions.keys(): # skip tokens if possible
                self.move_cursor()
                continue

            for func in self.parsing_functions[token_name]:
                func()
                if not self.do_move:
                    break
            

            self.move_cursor()
            iters+=1

        errors.developer_info(f"iters: {iters}")
        self.start = previous_start_position

        # * give warnings about experimental features
        if errors.USES_FEATURE["array"]:
            errors.experimental_warning("Arrays are an experimental feature that is not complete", ("Seg-faults","compilation errors","other memory related errors"))

        return self._tokens
    
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
    
    def check_group_lookahead(self, start_index: int, wanting: str) -> bool:
        '''check a group of tokens in a string seperated by spaces. This version has lookahead'''
        worked = self.check_group(start_index, wanting)
        if not worked:
            return False

        tokens = wanting.split(' ')
        tmp = self._cursor 
        st_tmp = self.start
        self._cursor += start_index+len(tokens)-1
        self.start = self._cursor
        
        while not self.isEOF():
            token_name = self.peek(0).name

            if token_name not in self.parsing_functions.keys(): # skip tokens if possible
                self.move_cursor()
                continue
        
            if self.peek(1).name=="SEMI_COLON" and token_name=="expr":
                break

            for func in self.parsing_functions[token_name]:
                func()
                if not self.do_move:
                    break
            self.move_cursor()

        self._cursor = tmp
        self.start = st_tmp
        self.do_move = True
  
        return self.check_group(start_index, wanting)

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
