from Ast.nodes.astnode import ASTNode


class Package(ASTNode):
    __slots__ = ('known_locations', 'modules')

    def __init__(self, pos, location):
        pass

    def copy(self):
        return self

    def fullfill_templates(self, func):
        return super().fullfill_templates(func)