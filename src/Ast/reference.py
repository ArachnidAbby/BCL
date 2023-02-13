from Ast import Ast_Types
from Ast.nodes import ExpressionNode
from Ast.nodes.commontypes import SrcPosition


class Ref(ExpressionNode):
    '''Variable Reference that acts like other `expr` nodes.
    It returns a ptr uppon `eval`'''
    __slots__ = ('var', )
    # name = "ref"
    assignable = True

    def __init__(self, pos: SrcPosition, var):
        super().__init__(pos)
        self.var = var

    def pre_eval(self, func):
        self.var.pre_eval(func)
        self.ret_type = Ast_Types.Reference(self.var.ret_type)
        self.ir_type = self.ret_type.ir_type

    def eval(self, func):
        return self.var.get_ptr(func)

    def get_var(self, func):
        return self.var.get_var(func)

    def get_value(self, func):
        return self.var

    def get_ptr(self, func):
        return self.var.get_ptr(func)

    def __repr__(self) -> str:
        return f"<Ref to '{self.var}'>"

    def __str__(self) -> str:
        return str(self.var)

    def as_type_reference(self):
        return Ast_Types.Reference(self.var.as_type_reference())
