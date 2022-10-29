from typing import Any, Iterator, Self, Tuple

from errors import error

from Ast.nodetypes import NodeTypes

from . import Ast_Types


class ASTNode:
    '''Most basic Ast-Node that all others inherit from. This just provides standardization between Ast-Nodes.'''
    __slots__ = ('name', 'position')
    is_operator = False
    type = NodeTypes.DEFAULT

    def __init__(self, position: Tuple[int,int, int], *args, **kwargs):
        #self.type = ""
        #self.name = ""
        self.position = position        # (line#, col#)

        self.init(*args, **kwargs)

    def is_expression(self):
        return self.type==NodeTypes.EXPRESSION
    
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
        self.ret_type = Ast_Types.AbstractType()
        self.position = position        # (line#, col#)

        self.init(*args, **kwargs)
    
    # todo: implement this functionality
    def __getitem__(self, name):
        '''get functionality from type (example: operators) automatically'''
        pass

class ContainerNode(ASTNode):
    '''A node consistening of other nodes. Containers do not directly do operations on these nodes'''
    __slots__ = ("children", )

    def __init__(self, position: Tuple[int,int, int], *args, **kwargs):
        self.children = list()
        super().__init__(position, *args, **kwargs)

    def __iter__(self) -> Iterator[Any]:
        yield from self.children

    def append_child(self, child: ASTNode|Self):
        self.children.append(child)

    def append_children(self, child: ASTNode|Self):
        '''possible to append 1 or more children'''
        if isinstance(child, ContainerNode):
            self.children += child.children
            return
        self.append_child(child)


class Block(ContainerNode):
    '''Provides a Block node that contains other `AST_NODE` objects'''
    __slots__ = ('variables', 'builder')
    type = NodeTypes.BLOCK
    name = "Block"

    def init(self):
        self.variables = dict() # {name: VarObj, ...}
        self.builder = None
    
    def pre_eval(self):
        for x in self.children:
            x.pre_eval()
    
    def eval(self, func):
        for x in self.children:
            x.eval(func)

    # def append_child(self, child: ASTNode):
    #     self.children.append(child)

    def get_variable(self, var_name: str):
        '''get variable by name'''
        return self.variables[var_name]

    def validate_variable(self, var_name: str) -> bool:
        '''Return if a variable already has a ptr'''
        return self.variables[var_name].ptr!=None

class StatementList(ContainerNode):
    __slots__ = ('children',)
    type = NodeTypes.STATEMENTLIST
    name = "StatementList"

    def init(self):
        self.children = list()

    # def append_child(self, child: ASTNode):
    #     if isinstance(child, StatementList):
    #         self.children+=child.children
    #     else:
    #         self.children.append(child)

    def pre_eval(self):
        for x in self.children:
            x.pre_eval()
    
    def eval(self, func):
        for x in self.children:
            x.eval(func)

class ExpressionList(ContainerNode):
    __slots__ = tuple()
    type = NodeTypes.STATEMENTLIST

    def init(self):
        self.name = "StatementList"

    def pre_eval(self):
        for x in self.children:
            x.pre_eval()
    
    def eval(self, func):
        for x in self.children:
            x.eval(func)

class ParenthBlock(ContainerNode):
    '''Provides a node for parenthesis as an expression or tuple'''
    __slots__ = ('ir_type', 'ret_type')
    type = NodeTypes.EXPRESSION

    def init(self):
        self.name = "Parenth"
        self.ir_type = Ast_Types.Void()
        
    def pre_eval(self):
        for x in self.children:
            x.pre_eval()
        
        # * tuples return `void` but an expr returns the same data as its child
        self.ret_type = self.children[0].ret_type if len(self.children)==1 else Ast_Types.Void()
        if self.ret_type!=Ast_Types.Void():
            self.ir_type = self.children[0].ir_type

    def __iter__(self) -> Iterator[Any]:
        yield from self.children
    
    def is_key_value_pairs(self) -> bool:
        '''check if all children are `KV_pair`s, this is useful for func definitions'''
        for x in self.children:
            if not isinstance(x, KeyValuePair):
                return False
        return True     

    def append_child(self, child: ASTNode):
        self.children.append(child)
        # if isinstance(child, str):
        #     error(f"Variable '{child}' not defined.", line = child.position)
        self.ret_type = self.children[0].ret_type if len(self.children)==1 else Ast_Types.Void()
    
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
        if self.value not in Ast_Types.Type_Base.types_dict:  # type: ignore
            error(f"unknown type '{self.value}'", line = self.position)
        
        return self.value

    def get_type(self) -> Any:
        '''Get and validate type'''
        return Ast_Types.Type_Base.types_dict[self.validate_type()]() # type: ignore # The types_dict returns an class that needs instantiated. Hence the extra ()
        
       
