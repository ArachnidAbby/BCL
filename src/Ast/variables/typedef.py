from Ast.Ast_Types.Type_Alias import Alias
from Ast.nodes.astnode import ASTNode
from Ast.nodes.commontypes import SrcPosition


class TypeDefinition(ASTNode):
    __slots__ = ('aliased', 'typ_name', 'module', 'typ')

    can_have_modifiers = True

    def __init__(self, pos: SrcPosition, name, aliased, module):
        super().__init__(pos)

        self.typ_name = name
        self.aliased = aliased
        self.module = module

        self.typ = Alias(module, name, None)
        module.create_type(self.typ_name, self.typ)
        module.add_alias_to_schedule(self)

    def copy(self):
        return TypeDefinition(self._position, self.typ_name,
                              self.aliased, self.module)

    def fullfill_templates(self, func):
        self.aliased.fullfill_templates(func)

    def scheduled(self, module):
        typ = self.aliased.as_type_reference(module, allow_generics=False)
        self.typ.set_type(typ, self.visibility)
