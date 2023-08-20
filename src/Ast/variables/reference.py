from Ast import Ast_Types
from Ast.Ast_Types import Type_Base
from Ast.nodes import ExpressionNode, block
from Ast.nodes.commontypes import Lifetimes, SrcPosition
from .varobject import VariableObj
from errors import error


class VariableRef(ExpressionNode):
    '''Get the value of a variable by name.
    Almost every "KEYWORD" the lexer spits out is
    turned into one of these. That is why it has methods like
    "as_type_reference" It needs to be versatile.
    Doing it in this way prevents the parser from needing to taking
    multiple passes
    '''
    __slots__ = ('block', 'var_name', 'from_global')
    assignable = True
    do_register_dispose = False

    def __init__(self, pos: SrcPosition, name: str, block):
        super().__init__(pos)
        self.var_name = name
        self.block = block

    def copy(self):
        last_block = None
        if len(block.Block.BLOCK_STACK) != 0:
            last_block = block.Block.BLOCK_STACK[-1]

        out = VariableRef(self._position, self.var_name, last_block)
        return out

    def reset(self):
        super().reset()
        self.from_global = None

    def fullfill_templates(self, func):
        return super().fullfill_templates(func)

    def pre_eval(self, func):
        if not self.block.validate_variable_exists(self.var_name, func.module):
            error(f"Undefined variable '{self.var_name}'", line=self.position)

        var = self.block.get_variable(self.var_name, func.module)
        self.ret_type = var.type
        if self.ret_type.is_void():
            error(f"undefined variable '{self.var_name}'", line=self.position)

    def eval_impl(self, func):
        var = self.block.get_variable(self.var_name, func.module)
        if not isinstance(var, VariableObj):
            error("Types or Functions cannot be used as values",
                  line=self.position)
        return var.get_value(func)

    def get_ptr(self, func):
        var = self.block.get_variable(self.var_name, func.module)
        if isinstance(var.type, Ast_Types.Reference):
            return func.builder.load(var.ptr)
        return var.ptr

    def get_var(self, func):
        old_block = self.block
        if self.block is None:
            self.block = func
        var = self.block.get_variable(self.var_name, func.module)
        self.block = old_block
        return var

    def get_lifetime(self, func):
        var = self.get_var(func)
        if var.is_arg and var.type.checks_lifetime:
            return Lifetimes.LONG
        return Lifetimes.FUNCTION

    def get_coupled_lifetimes(self, func) -> list:
        var = self.block.get_variable(self.var_name, func.module)
        if var.is_arg:
            return [var.arg_idx]

        return []

    def get_function(self, func):
        return func.module.get_function(self.var_name, self.position)

    def get_value(self, func):
        '''only important in references'''
        self.ret_type = self.ret_type.typ
        return self

    def as_type_reference(self, func, allow_generics=False):
        '''Get this variable's name as a Type
        This is useful for static type declaration.
        '''
        typ = func.get_type_by_name(self.var_name, self.position)()
        if typ.is_generic and not allow_generics:
            error(f"Type is generic. Add type params. {typ}",
                  line=self.position)

        return typ

    def __repr__(self) -> str:
        return f"<VariableRef to '{self.var_name}'>"

    def __str__(self) -> str:
        return str(self.var_name)

    def __hash__(self):
        return hash(self.var_name)

    def repr_as_tree(self) -> str:
        return self.create_tree("Variable Access",
                                name=self.var_name,
                                return_type=self.ret_type)
