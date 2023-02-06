'''Define basic classes for nodes. These are the most basic nodes such as the ASTNode baseclass.'''

from collections import deque
from typing import Any, Iterator, Protocol, Self, Tuple, Union

from Ast.nodetypes import NodeTypes
from errors import error

from . import Ast_Types

SrcPosition = tuple[int,int, int]
GenericNode = Union['ASTNode', 'ExpressionNode']

class ASTNode:
    '''Most basic Ast-Node that all others inherit from. This just provides standardization between Ast-Nodes.
     
    Methods required for classes inheriting this class:
    ====================================================
    * init -- method run uppon instantiation. This can take any # of args and kwargs
    * pre_eval -- run before eval(). Often used to validate certain conditions, such as a function or variable existing, return type, etc.
    * eval -- returns ir.Instruction object or None. This is used when construction final ir code.
    '''
    __slots__ = ('_position')

    is_operator: bool = False
    type: NodeTypes = NodeTypes.DEFAULT
    name: str = "AST_NODE"

    def __init__(self, position: SrcPosition, *args, **kwargs):
        self._position = position        # (line#, col#, len)

        # self.init(*args, **kwargs)

    def is_expression(self):
        '''check whether or not a node is an expression'''
        return self.type==NodeTypes.EXPRESSION

    # def init(self, *args):
    #     '''initialize the node'''

    def pre_eval(self, func):
        '''pre eval step that is usually used to validate the contents of a node'''

    def eval(self, func):
        '''eval step, often returns ir.Instruction'''
    
    def merge_pos(self, positions: Tuple[SrcPosition, ...]) -> SrcPosition:
        new_pos = list(self._position)
        for x in positions:
            current_len = (new_pos[2]+new_pos[1]-1) # len of current position ptr
            end_pos = (x[1]-current_len)+x[2]
            new_pos[2] = end_pos
        
        return tuple(new_pos) # type: ignore
    
    @property
    def position(self) -> SrcPosition:
        return self._position

    @position.setter
    def position(self, val):
        self._position = val


class ExpressionNode(ASTNode):
    '''Acts as an Expression in the AST. This means it has a value and return type'''
    __slots__ = ("ret_type", "ir_type", "ptr")
    type = NodeTypes.EXPRESSION

    def __init__(self, position: SrcPosition, *args, **kwargs):
        self.ret_type = Ast_Types.Type()
        self._position = position
        self.ptr = None
        super().__init__(position, *args, **kwargs)

        # self.init(*args, **kwargs) # Info: this was running twice, keeping it just incase it was for a reason.
    
    # todo: implement this functionality
    def __getitem__(self, name):
        '''get functionality from type (example: operators) automatically'''

    def get_ptr(self, func):
        '''allocate to stack and get a ptr'''
        if self.ptr is None:
            self.ptr = func.create_const_var(self.ret_type)
            val = self.eval(func)
            func.builder.store(val, self.ptr)
        return self.ptr
    
    def as_type_reference(self):
        '''Get this expresion as the reference to a type'''
        error(f"invalid type: {str(self)}", line = self.position)

class ContainerNode(ASTNode):
    '''A node consistening of other nodes.
    Containers do not directly do operations on these nodes
    '''
    __slots__ = ("children", )

    def __init__(self, position: SrcPosition, *args, **kwargs):
        self.children: list = []
        super().__init__(position, *args, **kwargs)

    def __iter__(self) -> Iterator[Any]:
        yield from self.children

    def append_child(self, child: GenericNode):
        '''append child to container.'''
        self.children.append(child)

    def append_children(self, child: GenericNode|Self):
        '''possible to append 1 or more children'''
        if isinstance(child, ContainerNode):
            self.children += child.children
            return
        self.append_child(child)


class Block(ContainerNode):
    '''Provides a Block node that contains other `AST_NODE` objects'''
    __slots__ = ('variables', 'builder', 'last_instruction', 'ended')
    type = NodeTypes.BLOCK
    name = "Block"

    BLOCK_STACK: deque[Self] = deque()

    def __init__(self, pos: SrcPosition, *args, **kwargs):
        super().__init__(pos, *args, **kwargs)
        self.variables: dict[str, object] = {} # {name: VarObj, ...} -- recursive import uppon proper type annotation
        self.builder = None
        self.last_instruction = False
        self.ended = False

    def append_nested_vars(self):
        '''append vars for nested blocks'''
        if len(self.BLOCK_STACK)!=0:
            self.variables = {**self.variables, **self.BLOCK_STACK[-1].variables}
    
    def pre_eval(self, func):
        self.append_nested_vars()
        self.BLOCK_STACK.append(self)
        for x in self.children:
            x.pre_eval(func)
        self.BLOCK_STACK.pop()
    
    def eval(self, func):
        if len(self.children) == 0:
            self.last_instruction = func.ret_type.name!="void"
            return
        self.BLOCK_STACK.append(self)
        for x in self.children[0:-1]:
            x.eval(func)
            if func.has_return or self.ended:
                self.BLOCK_STACK.pop()
                return
        self.last_instruction = func.ret_type.name!="void"
        self.children[-1].eval(func)
        self.BLOCK_STACK.pop()

    def get_variable(self, var_name: str):
        '''get variable by name'''
        return self.variables[var_name]

    def validate_variable(self, var_name: str) -> bool:
        '''Return true if a variable already has a ptr'''
        return self.variables[var_name].ptr is not None # type: ignore
    
    def validate_variable_exists(self, var_name: str) -> bool:
        return var_name in self.variables.keys()

class ParenthBlock(ContainerNode):
    '''Provides a node for parenthesis as an expression or tuple'''
    __slots__ = ('ir_type', 'ret_type', 'in_func_call' , 'ptr')
    type = NodeTypes.EXPRESSION
    name = "Parenth"

    def __init__(self, pos: SrcPosition, *args, **kwargs):
        super().__init__(pos, *args, **kwargs)
        self.ir_type = Ast_Types.Void().ir_type
        self.in_func_call = False
        self.ptr = None
        self.ret_type = Ast_Types.Void()
        
    def pre_eval(self, func):
        for c, child in enumerate(self.children):
            child.pre_eval(func)
        
        # * tuples return `void` but an expr returns the same data as its child
        self.ret_type = self.children[0].ret_type if len(self.children)==1 else Ast_Types.Void()
        self.ir_type = self.ret_type.ir_type

    def __iter__(self) -> Iterator[Any]:
        yield from self.children
    
    def is_key_value_pairs(self) -> bool:
        '''check if all children are `KV_pair`s, this is useful for func definitions'''
        for x in self.children:
            if not isinstance(x, KeyValuePair):
                return False
        return True     

    def append_child(self, child: GenericNode):
        self.children.append(child)
        self.ret_type = self.children[0].ret_type if len(self.children)==1 else Ast_Types.Void()
        
    
    def _pass_as_pointer_changes(self, func):
        '''changes child elements to be passed as pointers if needed'''
        for c, child in enumerate(self.children):
            if self.in_func_call and (child.ret_type.pass_as_ptr or child.ret_type.name=='strlit'):
                ptr = child.get_ptr(func)
                self.children[c] = ptr
                continue
            self.children[c] = child.eval(func)

    def eval(self, func):
        self._pass_as_pointer_changes(func)
        if len(self.children)==1:
            return self.children[0]

    def __repr__(self) -> str:
        return f'<Parenth Block: \'({", ".join((repr(x) for x in self.children))})\'>'

    def get_ptr(self, func):
        '''allocate to stack and get a ptr'''
        if self.type != NodeTypes.EXPRESSION:
            error("Cannot get a ptr to a set of parentheses with more than one value", line = self.position)
        # print(self.ret_type)
        if self.ptr is None:
            self.ptr = func.create_const_var(self.ret_type)
            val = self.eval(func)
            
            func.builder.store(val, self.ptr)
        return self.ptr
class KeyValuePair(ASTNode):
    '''Key-Value pairs for use in things like structs, functions, etc.'''
    __slots__ = ('key', 'value')
    type = NodeTypes.KV_PAIR
    name = "kv_pair"

    def __init__(self, pos: SrcPosition, k, v):
        super().__init__(pos)
        self.key      = k
        self.value    = v
    
    def validate_type(self): # TODO: REMOVE, DUPLICATE
        return self.value.as_type_reference()

    def get_type(self) -> Any:
        '''Get and validate type'''
        return self.value.as_type_reference()

    @property
    def position(self) -> SrcPosition:
        return self.merge_pos((self.value.position, ))
        
       
