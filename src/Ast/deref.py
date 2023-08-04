from Ast.Ast_Types.Type_Reference import Reference
from Ast.nodes.commontypes import Lifetimes
from Ast.nodes.expression import ExpressionNode


class Deref(ExpressionNode):
    __slots__ = ('ref', 'assignable')

    do_register_dispose = False

    def __init__(self, pos, ref):
        super().__init__(pos)

        self.ref = ref
        self.assignable = True

    def copy(self):
        return Deref(self._position, self.ref.copy())

    def fullfill_templates(self, func):
        self.ref.fullfill_templates(func)

    def post_parse(self, func):
        self.ref.post_parse(func)

    def pre_eval(self, func):
        self.ref.pre_eval(func)

        self.ret_type = self.ref.ret_type.get_deref_return(func, self.ref)
        # if isinstance(self.ret_type, Reference):

    def eval_impl(self, func):
        return self.ref.ret_type.deref(func, self.ref)

    def get_lifetime(self, func):
        return self.ref.get_lifetime(func)

    def get_ptr(self, func):
        if isinstance(self.ret_type, Reference):
            return self.eval(func)
        return self.ref.eval(func)
