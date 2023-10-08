import errors
from Ast.Ast_Types.Type_Alias import Alias
from Ast.generics import GenericSpecify
from Ast.nodes.astnode import ASTNode
from Ast.nodes.block import Block
from Ast.nodes.commontypes import SrcPosition
from Ast.variables.reference import VariableRef


class TypeDefinition(ASTNode):
    __slots__ = ('aliased', 'typ_name', 'module', 'typ',
                 'is_generic', 'params', 'original_name',
                 'internal_block')

    can_have_modifiers = True

    def __init__(self, pos: SrcPosition, name, aliased, module,
                 register=True):
        super().__init__(pos)

        self.original_name = name

        if isinstance(name, VariableRef):
            self.is_generic = False
            self.typ_name = name.var_name
            self.params = {}  # type params
        if isinstance(name, GenericSpecify):  # generic
            self.is_generic = True
            self.typ_name = name.left.var_name
            # type params
            self.params = {x.var_name: (None, None) for x in name.params}

        # A a fake set of `{}` that encapsulate the node that creates the
        # aliased type.
        # This is to allow the generic names to be resolved.
        inner_block_broken = Block(name.position, self)
        inner_block_broken.append_child(aliased)

        # copying fixes a lot of references to blocks that are set to None
        # by default during parsing. This is easier than recursively descending
        # the nodes manually.
        self.internal_block = inner_block_broken.copy()
        self.internal_block.parent = self

        self.aliased = self.internal_block.children[0]
        self.module = module

        self.typ = Alias(module, name, None, self)
        self.typ.is_generic = self.is_generic

        if register:
            module.create_type(self.typ_name, self.typ)
            module.add_alias_to_schedule(self)

    def get_variable(self, var_name, module=None):
        '''Methods use this to get the names of types
        '''
        if var_name in self.params.keys():
            var = self.params[var_name][0]
            return var
        elif module is not None:
            return module.get_global(var_name)

    def validate_variable_exists(self, var_name, module=None):
        if var_name in self.params.keys():
            return self.get_variable(var_name, module)
        elif module is not None:
            return module.get_global(var_name)

    def get_type_by_name(self, var_name, pos):
        if var_name in self.params.keys():
            return self.params[var_name][0]

        return self.module.get_type_by_name(var_name, pos)

    def copy(self):
        return TypeDefinition(self._position, self.original_name,
                              self.aliased, self.module, register=False)

    def fullfill_templates(self, func):
        if not self.is_generic:
            self.aliased.fullfill_templates(func)
            return

        for ver in self.typ.versions.values():
            errors.templating_stack.append(ver[3])
            ver[2].fullfill_templates(func)
            del errors.templating_stack[-1]

    def scheduled(self, module):
        if not self.is_generic:
            typ = self.aliased.as_type_reference(module, allow_generics=False)
            self.typ.set_type(typ, self.visibility)

        for ver in self.typ.versions.values():
            errors.templating_stack.append(ver[3])
            ver[2].scheduled(module)
            del errors.templating_stack[-1]
