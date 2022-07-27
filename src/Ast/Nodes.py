from typing import List, Tuple

from llvmlite import ir


class AST_NODE:
    '''Most basic Ast-Node that all others inherit from. This just provides standardization between Ast-Nodes.'''
    __slots__ = ['name', 'type', 'children', 'position', 'token', "ret_type", "is_operator"]

    def __init__(self, position: Tuple[int,int], token: str, children: None|List = None, *args):
        self.type = ""
        self.name = ""
        self.ret_type = ""
        self.position = position        # (line#, col#)
        self.token = token  # source code of this NODE.
        self.children = [] if children==None else children
        self.is_operator = False


        self.init(*args)
    
    def init(self):
        pass

    def eval(self, func):
        pass

    # todo: rewrite and make this useful    
    def show_er(self, source: List[str]) -> str:
        '''Show an error, 
            source: file's source seperated by lines.
        '''
        output = source[self.position[0]]+f'\n{" "*(self.position[1]-1)}'+f"{'^'*len(self.token)}"
        return output


class Block(AST_NODE):
    '''Provides a Block node that contains other `AST_NODE` objects'''
    __slots__ = ['variables', 'builder']

    def init(self):
        self.name = "Block"
        self.type = "Block"
        self.ret_type = "void"

        self.variables = dict() # {name: (ptr, type_str), ...}
        self.builder = None
    
    def append_child(self, child: AST_NODE):
        self.children.append(child)

class ParenthBlock(AST_NODE):
    '''Provides a node for parenthesis as an expression or tuple'''
    __slots__ = []

    def init(self):
        self.name = "Parenth"
        self.type = "Parenth"
        
        # * tuples return `void` but an expr returns the same data as its child
        self.ret_type = self.children[0].ret_type if len(self.children)==1 else "void"
        # print(len(self.children)==1)
    
    def append_child(self, child: AST_NODE):
        self.children.append(child)
        self.ret_type = self.children[0].ret_type if len(self.children)==1 else "void"
    
    def eval(self, func):
        for c, child in enumerate(self.children):
            self.children[c] = child.eval(func)
        
        if len(self.children)==1:
            return self.children[0]