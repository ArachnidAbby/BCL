from Ast import Ast_Types
from Ast.functions import functionobject
from Ast.nodes import ExpressionNode
from Ast.nodes.commontypes import SrcPosition
from errors import error


class VariableRef(ExpressionNode):
    '''Get the value of a variable by name.
    Almost every "KEYWORD" the lexer spits out is
    turned into one of these. That is why it has methods like
    "as_type_reference" It needs to be versatile.
    Doing it in this way prevents the parser from needing to taking
    multiple passes
    '''
    __slots__ = ('block', 'var_name')
    assignable = True

    def __init__(self, pos: SrcPosition, name: str, block):
        super().__init__(pos)
        self.var_name = name
        self.block = block

    def pre_eval(self, func):
        if not self.block.validate_variable_exists(self.var_name):
            error(f"Undefined variable '{self.var_name}'", line=self.position)

        self.ret_type = self.block.get_variable(self.var_name).type
        if self.ret_type.is_void():
            error(f"undefined variable '{self.var_name}'", line=self.position)

        self.ir_type = self.ret_type.ir_type

    def eval(self, func):
        return self.block.get_variable(self.var_name).get_value(func)

    def get_ptr(self, func):
        return self.block.get_variable(self.var_name).ptr

    def get_var(self, func):
        return self.block.get_variable(self.var_name)

    def get_value(self, func):
        '''only important in references'''
        self.ret_type = self.ret_type.typ
        return self

    def as_type_reference(self):
        '''Get this variable's name as a Type
        This is useful for static type declaration.
        '''
        if self.var_name in Ast_Types.types_dict:
            return Ast_Types.types_dict[self.var_name]()
        else:
            error(f"Could not find type: {self.var_name}", line=self.position)

    def as_func_reference(self):
        '''Get this variable's name as the name of a function
        Not yet used, but I predict it will be needed
        '''  # TODO KEEP UPDATED
        if self.var_name in functionobject.functions.keys():
            return functionobject.functions[self.var_name]
        else:
            error(f"Could not find function: {self.var_name}",
                  line=self.position)

    def __repr__(self) -> str:
        return f"<VariableRef to '{self.var_name}'>"

    def __str__(self) -> str:
        return str(self.var_name)

    def __hash__(self):
        return hash(self.var_name)
