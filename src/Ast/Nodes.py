from copy import copy
from typing import List, Tuple
from Errors import error

from llvmlite import ir


class AST_NODE:
    '''Most basic Ast-Node that all others inherit from. This just provides standardization between Ast-Nodes.'''
    __slots__ = ['name', 'type', 'children', 'position', "ret_type", "is_operator"]

    def __init__(self, position: Tuple[int,int, int], children: None|List = None, *args):
        self.type = ""
        self.name = ""
        self.ret_type = "pre-eval ret type"
        self.position = position        # (line#, col#)
        self.children = list() if children==None else children
        self.is_operator = False


        self.init(*args)
    
    def init(self):
        pass

    def pre_eval(self):
        '''pre evaluation step that will likely be to determine ret_type of nodes that don't have a definite return type'''
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
    
    def pre_eval(self):
        for x in self.children:
            if isinstance(x, str):
                error(f"Variable '{x}' not defined.")
            x.pre_eval()

    def append_child(self, child: AST_NODE):
        self.children.append(child)

class ParenthBlock(AST_NODE):
    '''Provides a node for parenthesis as an expression or tuple'''
    __slots__ = ['ir_type']

    def init(self):
        self.name = "Parenth"
        self.type = "Parenth"
        self.ir_type = "INVALID"
        
    def pre_eval(self):
        for x in self.children:
            x.pre_eval()
        
        # * tuples return `void` but an expr returns the same data as its child
        self.ret_type = self.children[0].ret_type if len(self.children)==1 else "void"
        if self.ret_type!="void":
            self.ir_type = self.children[0].ir_type

    def is_key_value_pairs(self):
        '''check if all children are `KV_pair`s, this is useful for func definitions'''
        for x in self.children:
            if not isinstance(x, KeyValuePair):
                return False
        return True        

    def append_child(self, child: AST_NODE):
        self.children.append(child)
        if isinstance(child, str):
            error(f"Variable '{child}' not defined.")
        self.ret_type = self.children[0].ret_type if len(self.children)==1 else "void"
    
    def eval(self, func):
        for c, child in enumerate(self.children):
            self.children[c] = child.eval(func)
        
        if len(self.children)==1:
            return self.children[0]

class KeyValuePair(AST_NODE):
    '''For now, it does nothing special'''
    __slots__ = ['key', 'value']

    def init(self, k, v):
        self.name = "kv_pair"
        self.type = "kv_pair"
        self.ret_type = "KV_Pair"

        self.key = k
        self.value = v
