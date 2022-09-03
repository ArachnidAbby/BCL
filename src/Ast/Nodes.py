from typing import Tuple
from Ast.Node_Types import NodeTypes
from Ast.Ast_Types.Utils import Types

from Errors import error


class AST_NODE:
    '''Most basic Ast-Node that all others inherit from. This just provides standardization between Ast-Nodes.'''
    __slots__ = ('name', 'type', 'position', "ret_type", "is_operator")

    def __init__(self, position: Tuple[int,int, int], *args, **kwargs):
        self.type = ""
        self.name = ""
        self.ret_type = Types.UNKNOWN
        self.position = position        # (line#, col#)
        self.is_operator = False


        self.init(*args, **kwargs)
    
    def init(self):
        pass

    def pre_eval(self):
        '''pre evaluation step that will likely be to determine ret_type of nodes that don't have a definite return type'''
        pass

    def eval(self, func):
        pass

class Block(AST_NODE):
    '''Provides a Block node that contains other `AST_NODE` objects'''
    __slots__ = ('variables', 'builder', 'children')

    def init(self):
        self.name = "Block"
        self.type = NodeTypes.BLOCK
        self.ret_type = Types.VOID
        self.children = list()

        self.variables = dict() # {name: VarObj, ...}
        self.builder = None
    
    def pre_eval(self):
        for x in self.children:
            if isinstance(x, str):
                error(f"Variable '{x}' not defined.")
            x.pre_eval()
    
    def eval(self, func):
        for x in self.children:
            x.eval(func)

    def append_child(self, child: AST_NODE):
        self.children.append(child)

    def get_variable(self, var_name: str):
        '''get variable by name'''
        return self.variables[var_name]

    def validate_variable(self, var_name: str) -> bool:
        '''Return if a variable already has a ptr'''
        return self.variables[var_name].ptr!=None

class StatementList(AST_NODE):
    __slots__ = ('children',)

    def init(self):
        self.name = "StatementList"
        self.type = NodeTypes.STATEMENTLIST
        self.ret_type = Types.VOID
        self.children = list()

    def append_child(self, child: AST_NODE):
        if isinstance(child, StatementList):
            self.children+=child.children
        else:
            self.children.append(child)

    def pre_eval(self):
        for x in self.children:
            if isinstance(x, str):
                error(f"Variable '{x}' not defined.")
            x.pre_eval()
    
    def eval(self, func):
        for x in self.children:
            x.eval(func)

class ParenthBlock(AST_NODE):
    '''Provides a node for parenthesis as an expression or tuple'''
    __slots__ = ('ir_type', 'children')

    def init(self):
        self.name = "Parenth"
        self.type = NodeTypes.EXPRESSION
        self.ir_type = Types.UNKNOWN
        self.children = list()
        
    def pre_eval(self):
        for x in self.children:
            x.pre_eval()
        
        # * tuples return `void` but an expr returns the same data as its child
        self.ret_type = self.children[0].ret_type if len(self.children)==1 else Types.VOID
        if self.ret_type!=Types.VOID:
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
            error(f"Variable '{child}' not defined.", line = child.position)
        self.ret_type = self.children[0].ret_type if len(self.children)==1 else Types.VOID
    
    def eval(self, func):
        for c, child in enumerate(self.children):
            self.children[c] = child.eval(func)
        
        if len(self.children)==1:
            return self.children[0]

class KeyValuePair(AST_NODE):
    '''Key-Value pairs for use in things like structs, functions, etc.'''
    __slots__ = ('key', 'value', 'keywords')

    def init(self, k, v, keywords = False):
        self.name = "kv_pair"
        self.type = Types.KV_PAIR
        self.ret_type = Types.KV_PAIR
        self.keywords = keywords

        self.key = k
        self.value = v
    
    def validate_type(self) -> str:        
        if self.value.upper() not in Types._member_names_:
            error(f"unknown type '{self.value}'", line = self.position)
        
        return self.value
        
       
