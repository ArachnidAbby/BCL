import errors
from Ast import Ast_Types
from Ast.nodes import ASTNode, Block


class YieldStatement(ASTNode):
    __slots__ = ("value", )

    def __init__(self, pos, value):
        super().__init__(pos)
        self.value = value

    def post_parse(self, func):
        if not func.yields:
            func.yields = True
            func.ret_type = Ast_Types.GeneratorType(func, func.ret_type)
            func.yield_gen_type = func.ret_type

    def pre_eval(self, func):
        self.value.pre_eval(func)

        if func.yield_type is None:
            func.yield_type = self.value.ret_type
        elif func.yield_type != self.value.ret_type:
            errors.error("Yielded value of type " +
                         f"\"{str(self.value.ret_type)}\", expected " +
                         f"\"{str(func.yield_type)}\"",
                         line=self.value.position)

    def eval(self, func):
        orig_block_name = func.builder.block._name

        yield_after = func.builder.append_basic_block(
                f'{orig_block_name}.yield_after'
            )

        func.yield_after_blocks.append(yield_after)
        func.yield_gen_type.set_value(func, self.value.eval(func), yield_after)
        if not func.builder.block.is_terminated:
            func.builder.ret_void()
        func.builder.position_at_start(yield_after)
