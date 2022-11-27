'''Define basic classes for nodes. These are the most basic nodes such as the ASTNode baseclass.'''

from typing import Any, Iterator, Self, Tuple

from errors import error

from Ast.nodetypes import NodeTypes

from . import Ast_Types


class ASTNode:
    '''Most basic Ast-Node that all others inherit from. This just provides standardization between Ast-Nodes.
     
    Methods required for classes inheriting this class:
    ====================================================
    * init -- method run uppon instantiation. This can take any # of args and kwargs
    * pre_eval -- run before eval(). Often used to validate certain conditions, such as a function or variable existing, return type, etc.
    * eval -- returns ir.Instruction object or None. This is used when construction final ir code.
    '''
    __slots__ = ('name', 'position')

    is_operator = False
    type = NodeTypes.DEFAULT

    def __init__(self, position: Tuple[int,int, int], *args, **kwargs):
        self.position = position        # (line#, col#)

        self.init(*args, **kwargs)

    def is_expression(self):
        '''check whether or not a node is an expression'''
        return self.type==NodeTypes.EXPRESSION

    def init(self, *args):
        '''initialize the node'''

    def pre_eval(self):
        '''pre eval step that is usually used to validate the contents of a node'''

    def eval(self, func):
        '''eval step, often returns ir.Instruction'''


class ExpressionNode(ASTNode):
    '''Acts as an Expression in the AST. This means it has a value and return type'''
    __slots__ = ("ret_type", "ir_type")
    type = NodeTypes.EXPRESSION

    def __init__(self, position: Tuple[int,int, int], *args, **kwargs):
        super().__init__(position, *args, **kwargs)
        self.ret_type = Ast_Types.AbstractType()
        self.position = position        # (line#, col#)

        self.init(*args, **kwargs)
    
    # todo: implement this functionality
    def __getitem__(self, name):
        '''get functionality from type (example: operators) automatically'''

class ContainerNode(ASTNode):
    '''A node consistening of other nodes.
    Containers do not directly do operations on these nodes
    '''
    __slots__ = ("children", )

    def __init__(self, position: Tuple[int,int, int], *args, **kwargs):
        self.children = []
        super().__init__(position, *args, **kwargs)

    def __iter__(self) -> Iterator[Any]:
        yield from self.children

    def append_child(self, child: ASTNode):
        '''append child to container.'''
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
        self.variables = {} # {name: VarObj, ...}
        self.builder = None
    
    def pre_eval(self):
        for x in self.children:
            x.pre_eval()
    
    def eval(self, func):
        for x in self.children:
            x.eval(func)

    def get_variable(self, var_name: str):
        '''get variable by name'''
        return self.variables[var_name]

    def validate_variable(self, var_name: str) -> bool:
        '''Return if a variable already has a ptr'''
        return self.variables[var_name].ptr!=None
    
    def validate_variable_exists(self, var_name: str) -> bool:
        return var_name in self.variables.keys()

class StatementList(ContainerNode):
    __slots__ = ('children',)
    type = NodeTypes.STATEMENTLIST
    name = "StatementList"

    def init(self):
        self.children = list()

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
        # print(self.children)
        for x in self.children:
            if not isinstance(x, KeyValuePair):
                return False
        return True     

    def append_child(self, child: ASTNode):
        self.children.append(child)
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
        # if self.value not in Ast_Types.Type_Base.types_dict:  # type: ignore
        #     error(f"unknown type '{self.value}'", line = self.position)
        
        return self.value.value

    def get_type(self) -> Any:
        '''Get and validate type'''
        return self.value.value # type: ignore # The types_dict returns an class that needs instantiated. Hence the extra ()
        
       
