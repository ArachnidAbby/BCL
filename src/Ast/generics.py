
from Ast.nodes import block
from Ast.nodes.expression import ExpressionNode
import errors


class GenericSpecify(ExpressionNode):
    __slots__ = ('left', 'params', 'in_definition', 'block')

    def __init__(self, pos, left, params, module, block):
        super().__init__(pos)
        self.left = left
        self.params = params
        self.in_definition = False
        self.block = block
        # module.add_template_to_schedule(self)

    # def get_type_by_name(self, name, pos):

    def copy(self):
        last_block = None
        if len(block.Block.BLOCK_STACK) != 0:
            last_block = block.Block.BLOCK_STACK[-1]
        return GenericSpecify(self._position, self.left.copy(), self.params.copy(), None, last_block)

    def fullfill_templates(self, func):
        self.left.fullfill_templates(func)
        self.params.fullfill_templates(func)
        self.as_type_reference(func)

    def post_parse(self, func):
        # if self.in_definition:
        #     return
        self.left.post_parse(func)
        self.params.post_parse(func)

    def scheduled(self, module):
        if self.in_definition:
            return
        self.as_type_reference(module)

    def eval(self, func):
        errors.error("Cannot use a type as an expression",
                     line=self.position)

    def get_var(self, func):
        return self

    def as_type_reference(self, func, allow_generics=False):
        typ = self.left.as_type_reference(func, allow_generics=True)
        return typ.pass_type_params(func, self.params.children, self.params.children[0].position)

    def __str__(self) -> str:
        return f"{self.left}::<{self.params}>"

    def get_position(self):
        # print(self._position)
        return self.merge_pos((self._position, self.params.position))
