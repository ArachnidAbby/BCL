import errors
from Ast import Ast_Types
from Ast.functions.functionobject import functionsdict
from Ast.nodes import ExpressionNode, ParenthBlock
from Ast.nodes.commontypes import SrcPosition


# TODO: should be turned into an operator and use a function type
class FunctionCall(ExpressionNode):
    '''Defines a function in the IR'''
    __slots__ = ('ir_type', 'paren', 'function', 'args_types', "func_name")
    # name = "funcCall"

    def __init__(self, pos: SrcPosition, name: str, parenth: ParenthBlock):
        super().__init__(pos)
        self.func_name = name
        self.ret_type = Ast_Types.Void()
        self.paren = parenth

    def _check_function_exists(self):
        '''ensure a function exists and the correct form of it exists'''
        if self.func_name not in functionsdict \
           or self.args_types not in functionsdict[self.func_name]:
            args_for_error = ','.join([str(x) for x in self.args_types])
            errors.error(f"function '{self.func_name}({args_for_error})' was never defined", line=self.position)

    def pre_eval(self, func):
        if isinstance(self.paren, ParenthBlock):
            self.paren.in_func_call = True
        self.paren.pre_eval(func)

        self.args_types = tuple([x.ret_type for x in self.paren])
        self._check_function_exists()

        self.ret_type = functionsdict[self.func_name][self.args_types].ret_type
        self.ir_type = (self.ret_type).ir_type
        self.function = functionsdict[self.func_name][self.args_types]

    def eval(self, func):
        x = self.paren.eval(func)
        if isinstance(self.paren, ParenthBlock):
            args = self.paren.children
        else:
            args = [x]
        return self.function.call(func, args)
