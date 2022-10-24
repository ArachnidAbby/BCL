from typing import Any, Iterator, Tuple

from Errors import error

from Ast.Node_Types import NodeTypes

from . import Ast_Types


class ASTNode:
    '''Most basic Ast-Node that all others inherit from. This just provides standardization between Ast-Nodes.'''
    __slots__ = ('name', 'position')
    is_operator = False
    type = ""

    def __init__(self, position: Tuple[int,int, int], *args, **kwargs):
        #self.type = ""
        #self.name = ""
        self.position = position        # (line#, col#)

        self.init(*args, **kwargs)
    
    def init(self):
        pass

    def pre_eval(self):
        '''pre evaluation step that will likely be to determine ret_type of nodes that don't have a definite return type'''
        pass

    def eval(self, func):
        pass


class ExpressionNode(ASTNode):
    '''Acts as an Expression in the AST. This means it has a value and return type'''
    __slots__ = ("ret_type", "ir_type")
    type = NodeTypes.EXPRESSION

    def __init__(self, position: Tuple[int,int, int], *args, **kwargs):
        #self.name = ""
        self.ret_type = Ast_Types.Type_Base.AbstractType()
        self.position = position        # (line#, col#)

        self.init(*args, **kwargs)
    
    # todo: implement this functionality
    def __getitem__(self, name):
        '''get functionality from type (example: operators) automatically'''
        pass

class Block(ASTNode):
    '''Provides a Block node that contains other `AST_NODE` objects'''
    __slots__ = ('variables', 'builder', 'children')
    type = NodeTypes.BLOCK

    def init(self):
        self.name = "Block"
        self.children = list()

        self.variables = dict() # {name: VarObj, ...}
        self.builder = None
    
    def pre_eval(self):
        for x in self.children:
            x.pre_eval()
    
    def eval(self, func):
        for x in self.children:
            x.eval(func)

    def append_child(self, child: ASTNode):
        self.children.append(child)

    def get_variable(self, var_name: str):
        '''get variable by name'''
        return self.variables[var_name]

    def validate_variable(self, var_name: str) -> bool:
        '''Return if a variable already has a ptr'''
        return self.variables[var_name].ptr!=None

class StatementList(ASTNode):
    __slots__ = ('children',)
    type = NodeTypes.STATEMENTLIST

    def init(self):
        self.name = "StatementList"
        self.children = list()

    def append_child(self, child: ASTNode):
        if isinstance(child, StatementList):
            self.children+=child.children
        else:
            self.children.append(child)

    def pre_eval(self):
        for x in self.children:
            x.pre_eval()
    
    def eval(self, func):
        for x in self.children:
            x.eval(func)

class ExpressionList(ASTNode):
    __slots__ = ('children',)
    type = NodeTypes.STATEMENTLIST

    def init(self):
        self.name = "StatementList"
        self.children = list()

    def append_child(self, child: ASTNode):
        self.children.append(child)

    def pre_eval(self):
        for x in self.children:
            x.pre_eval()
    
    def eval(self, func):
        for x in self.children:
            x.eval(func)

class ParenthBlock(ASTNode):
    '''Provides a node for parenthesis as an expression or tuple'''
    __slots__ = ('ir_type', 'children', 'ret_type')
    type = NodeTypes.EXPRESSION

    def init(self):
        self.name = "Parenth"
        self.ir_type = Ast_Types.Void()
        self.children = list()
        
    def pre_eval(self):
        for x in self.children:
            x.pre_eval()
        
        # * tuples return `void` but an expr returns the same data as its child
        self.ret_type = self.children[0].ret_type if len(self.children)==1 else Ast_Types.Type_Void.Void()
        if self.ret_type!=Ast_Types.Void():
            self.ir_type = self.children[0].ir_type

    def __iter__(self) -> Iterator[Any]:
        yield from self.children
    
    def is_key_value_pairs(self):
        '''check if all children are `KV_pair`s, this is useful for func definitions'''
        for x in self.children:
            if not isinstance(x, KeyValuePair):
                return False
        return True     

    def append_child(self, child: ASTNode):
        self.children.append(child)
        # if isinstance(child, str):
        #     error(f"Variable '{child}' not defined.", line = child.position)
        self.ret_type = self.children[0].ret_type if len(self.children)==1 else Ast_Types.Type_Void.Void()
    
    def eval(self, func):
        for c, child in enumerate(self.children):
            self.children[c] = child.eval(func)
        
        if len(self.children)==1:
            return self.children[0]

    def __repr__(self) -> str:
        return f'<Parenth Block: \'({", ".join((repr(x) for x in self.children))})\'>'

class KeyValuePair(ASTNode):
    '''Key-Value pairs for use in things like structs, functions, etc.'''
    __slots__ = ('key', 'value', 'keywords')
    type = 'kv pair'

    def init(self, k, v, keywords = False):
        self.name = "kv_pair"
        self.keywords = keywords

        self.key = k
        self.value = v
    
    def validate_type(self) -> str:        
        if self.value not in Ast_Types.Type_Base.types_dict:
            error(f"unknown type '{self.value}'", line = self.position)
        
        return self.value

    def get_type(self) -> Any:
        '''Get and validate type'''
        return Ast_Types.Type_Base.types_dict[self.validate_type()]() # The types_dict returns an class that needs instantiated. Hence the extra ()
        
       
