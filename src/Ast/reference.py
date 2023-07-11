from Ast import Ast_Types
from Ast.nodes import ExpressionNode
from Ast.nodes.commontypes import SrcPosition


class Ref(ExpressionNode):
    '''Variable Reference that acts like other `expr` nodes.
    It returns a ptr uppon `eval`'''
    __slots__ = ('var', )
    assignable = True
    do_register_dispose = False

    def __init__(self, pos: SrcPosition, var):
        super().__init__(pos)
        self.var = var

    def pre_eval(self, func):
        self.var.pre_eval(func)
        if isinstance(self.var.ret_type, Ast_Types.Reference):
            self.ret_type = self.var.ret_type
        else:
            self.ret_type = Ast_Types.Reference(self.var.ret_type)

    def eval_impl(self, func):
        # self.var.ret_type.add_ref_count(func, self.var)
        # self.var.overwrite_eval = True
        return self.var.get_ptr(func)

    def get_var(self, func):
        return self.var.get_var(func)

    def get_value(self, func):
        return self.var

    def get_ptr(self, func):
        return self.eval(func)

    def __repr__(self) -> str:
        return f"<Ref to '{self.var}'>"

    def __str__(self) -> str:
        return f"&{str(self.var)}"

    def as_type_reference(self, func, allow_generics=False):
        return Ast_Types.Reference(self.var.as_type_reference(func, allow_generics=allow_generics))

    def repr_as_tree(self) -> str:
        return self.create_tree("Reference",
                                var=self.var,
                                return_type=self.ret_type)

    def get_position(self) -> SrcPosition:
        return self.merge_pos((self._position,
                               self.var.position))
