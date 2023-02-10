import errors
from Ast.nodes import ASTNode, ExpressionNode
from Ast.nodes.commontypes import SrcPosition


class ReturnStatement(ASTNode):
    __slots__ = ('expr')
    # type = NodeTypes.STATEMENT
    # name = "return"

    def __init__(self, pos: SrcPosition, expr: ExpressionNode):
        self._position = pos
        self.expr = expr

    def pre_eval(self, func):
        self.expr.pre_eval(func)

    def _check_valid_type(self, func):
        if self.expr.ret_type != func.ret_type:
            errors.error(f"Funtion, \"{func.func_name}\", has a return type" +
                         f" of '{func.ret_type}'. Return statement returned" +
                         f" '{self.expr.ret_type}'", line=self.position)

    def eval(self, func):
        func.has_return = True
        self._check_valid_type(func)

        if func.ret_type.is_void():
            func.builder.ret_void()
        else:
            func.builder.ret(self.expr.eval(func))
