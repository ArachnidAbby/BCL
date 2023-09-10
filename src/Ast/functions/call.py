from Ast import Ast_Types
from Ast.Ast_Types.Type_Function import FunctionGroup
from Ast.math import MemberAccess
from Ast.nodes import ExpressionNode, ParenthBlock
from Ast.nodes.commontypes import Lifetimes, SrcPosition


class FunctionCall(ExpressionNode):
    '''Defines a function in the IR'''
    __slots__ = ('paren', 'function', 'args_types', "func_name",
                 "dot_call", "combined_args")

    def __init__(self, pos: SrcPosition, name, parenth: ParenthBlock):
        super().__init__(pos)
        self.func_name = name
        self.ret_type = Ast_Types.Void()
        self.paren = parenth
        self.args_types = None
        self.function = None
        self.combined_args = False

    def copy(self):
        out = FunctionCall(self._position, self.func_name.copy(), self.paren.copy())
        return out

    def reset(self):
        self.paren.reset()
        self.func_name.reset()
        self.args_types = None
        self.ret_type = Ast_Types.Void()

    def fullfill_templates(self, func):
        self.paren.fullfill_templates(func)
        self.func_name.fullfill_templates(func)

    def post_parse(self, func):
        self.paren.post_parse(func)
        self.func_name.post_parse(func)
        func.lifetime_checked_nodes.append(self)

    def pre_eval(self, func):
        if isinstance(self.paren, ParenthBlock):
            self.paren.in_func_call = True
        self.paren.pre_eval(func)

        if self.args_types is None:
            self.args_types = tuple([x.ret_type for x in self.paren])

        self.func_name.pre_eval(func)
        # * Special "dot call" syntax
        if isinstance(self.func_name, MemberAccess) and \
                self.func_name.using_global(func) and not \
                self.combined_args:
            self.combined_args = True
            data = self.func_name.lhs
            data = data.children if isinstance(data, ParenthBlock) else [data]
            self.paren.children = data + self.paren.children

        self.ret_type = self.func_name.ret_type.get_op_return(func,
                                                              "call",
                                                              self.func_name,
                                                              self.paren)

        self.function = self.func_name.get_var(func).ret_type
        self.resolve_lifetime_coupling(func)

    def resolve_lifetime_coupling(self, func):
        # if self.function is None:
        #     self.function = self.func_name.get_var(func).ret_type
        if isinstance(self.function, FunctionGroup):
            coupling_func = self.function.get_function(func, self.func_name, self.paren)
        else:
            coupling_func = self.function

        arg_ids = []

        childs = self.paren.children
        if isinstance(self.func_name, MemberAccess) and coupling_func.is_method:
            childs = [self.func_name.lhs] + childs

        for idx, child in enumerate(childs):
            lifetimes = child.get_coupled_lifetimes(func)
            for life in lifetimes:
                # if isinstance(life, list):
                #     print("AHAHAHALHAJHDJAD:LKJ")
                #     print(life)
                #     continue
                arg_ids.append((idx, life))

        func.function_ty.coupled_functions.append((coupling_func, tuple(arg_ids), self))

    def eval_impl(self, func):
        return self.function.call(func, self.func_name, self.paren)

    def get_lifetime(self, func):
        return Lifetimes.FUNCTION

    def repr_as_tree(self) -> str:
        return self.create_tree("Function Call",
                                name=self.func_name,
                                paren=self.paren)
