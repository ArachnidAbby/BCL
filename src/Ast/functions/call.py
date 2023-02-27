import errors
from Ast import Ast_Types
from Ast.nodes import ExpressionNode, ParenthBlock
from Ast.nodes.commontypes import SrcPosition


class FunctionCall(ExpressionNode):
    '''Defines a function in the IR'''
    __slots__ = ('paren', 'function', 'args_types', "func_name")

    def __init__(self, pos: SrcPosition, name: str, parenth: ParenthBlock):
        super().__init__(pos)
        self.func_name = name
        self.ret_type = Ast_Types.Void()
        self.paren = parenth

    # def _check_function_exists(self, func):
    #     '''ensure a function exists and the correct form of it exists'''
    #     functions = func.module.get_function(self.func_name,  self.position)
    #     if not :

    def pre_eval(self, func):
        if isinstance(self.paren, ParenthBlock):
            self.paren.in_func_call = True
        self.paren.pre_eval(func)

        self.args_types = tuple([x.ret_type for x in self.paren])
        # self._check_function_exists(func)

        function_name = func.module.get_function(self.func_name, self.position)
        self.function = func.module.get_func_from_dict(self.func_name,
                                                       function_name,
                                                       self.args_types,
                                                       self.position)

        self.ret_type = self.function.ret_type

    def eval(self, func):
        x = self.paren.eval(func)
        if isinstance(self.paren, ParenthBlock):
            args = self.paren.children
        else:
            args = [x]
        return self.function.call(func, args)

    def repr_as_tree(self) -> str:
        return self.create_tree("Function Call",
                                name=self.func_name,
                                paren=self.paren)
