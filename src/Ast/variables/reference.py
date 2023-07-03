from Ast import Ast_Types
from Ast.Ast_Types import Type_Base
from Ast.nodes import ExpressionNode
from Ast.nodes.commontypes import SrcPosition
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

    def __init__(self, pos: SrcPosition, name: str, block):
        super().__init__(pos)
        self.var_name = name
        self.block = block

    def pre_eval(self, func):
        if not self.block.validate_variable_exists(self.var_name, func.module):
            error(f"Undefined variable '{self.var_name}'", line=self.position)

        var = self.block.get_variable(self.var_name, func.module)
        self.ret_type = var.type
        if self.ret_type.is_void():
            error(f"undefined variable '{self.var_name}'", line=self.position)

    def eval(self, func):
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
        return self.block.get_variable(self.var_name, func.module)

    def get_function(self, func):
        return func.module.get_function(self.var_name, self.position)

    def get_value(self, func):
        '''only important in references'''
        self.ret_type = self.ret_type.typ
        return self

    def as_type_reference(self, func):
        '''Get this variable's name as a Type
        This is useful for static type declaration.
        '''
        return func.module.get_type(self.var_name, self.position)()

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
