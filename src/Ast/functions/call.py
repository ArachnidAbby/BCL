import errors
from Ast import Ast_Types
from Ast.math import MemberAccess
from Ast.nodes import ContainerNode, ExpressionNode, ParenthBlock
from Ast.nodes.commontypes import SrcPosition


class FunctionCall(ExpressionNode):
    '''Defines a function in the IR'''
    __slots__ = ('paren', 'function', 'args_types', "func_name",
                 "dot_call")

    def __init__(self, pos: SrcPosition, name, parenth: ParenthBlock):
        super().__init__(pos)
        self.func_name = name
        self.ret_type = Ast_Types.Void()
        self.paren = parenth

    def pre_eval(self, func):
        if isinstance(self.paren, ParenthBlock):
            self.paren.in_func_call = True
        self.paren.pre_eval(func)

        self.args_types = tuple([x.ret_type for x in self.paren])

        self.func_name.pre_eval(func)
        if isinstance(self.func_name, MemberAccess) and \
                self.func_name.using_global(func):
            data = self.func_name.lhs
            data = data.children if isinstance(data, ParenthBlock) else [data]
            self.paren.children = data + self.paren.children

        self.ret_type = self.func_name.ret_type.get_op_return("call", None,
                                                              self.paren)

        self.function = self.func_name.get_var(func).ret_type

    def eval(self, func):
        return self.function.call(func, self.func_name, self.paren)

    def repr_as_tree(self) -> str:
        return self.create_tree("Function Call",
                                name=self.func_name,
                                paren=self.paren)
