
from Ast.nodes.expression import ExpressionNode
import errors


class GenericSpecify(ExpressionNode):
    __slots__ = ('left', 'params')

    def __init__(self, pos, left, params):
        super().__init__(pos)
        self.left = left
        self.params = params

    def eval(self, func):
        errors.error("Cannot use a type as an expression",
                     line=self.position)

    def get_var(self, func):
        return self

    # def get_namespace_name(func, right, pos):


    def as_type_reference(self, func, allow_generics=False):
        typ = self.left.as_type_reference(func, allow_generics=True)
        return typ.pass_type_params(func, self.params.children, self.params.children[0].position)

    def __str__(self) -> str:
        return f"{self.left}::<{self.params}>"

    def get_position(self):
        # print(self._position)
        return self.merge_pos((self._position, self.params.position))
