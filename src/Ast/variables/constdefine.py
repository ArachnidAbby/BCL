from Ast.nodes.astnode import ASTNode


# TODO: implement this.
class ConstDef(ASTNode):
    __slots__ = ()

    def __init__(self, pos, name, value):
        # check name is valid

        # check value is literal

        pass

    def post_parse(self, func):
        pass

    def pre_eval(self, func):
        pass

    def eval_impl(self, func):
        pass
