import errors
from Ast.Ast_Types.Type_Base import Type
from Ast.Ast_Types.Type_Void import Void

# from Ast.nodes.commontypes import SrcPosition


class Alias(Type):
    __slots__ = ('module', 'aliased_typ', 'name',
                 'typ_name', 'is_public', "is_generic",
                 "versions", "definition")

    def __init__(self, module, name, aliased, definition):
        self.aliased_typ = aliased
        self.typ_name = name
        self.name = ""
        self.module = module
        self.is_public = False
        self.definition = definition
        self.is_generic = False
        self.versions = {}

    def set_type(self, typ, public):
        self.aliased_typ = typ
        self.name = typ.name
        self.is_public = public

    def pass_type_params(self, func, params, pos):
        from Ast.variables.reference import VariableRef

        params_types = []

        for ty in params:
            params_types.append(ty.as_type_reference(func))

        params = tuple(params_types)

        if len(params) != len(self.definition.params):
            errors.error("Invalid Generic arguments. Not enough args",
                         line=pos)

        if Void() in params:
            return self

        if params in self.versions.keys():
            return self.versions[params][0]

        new_name = f"{self.typ_name}::<{', '.join([str(x) for x in params])}>"

        name_var = VariableRef(pos, new_name, None)

        generic_args = {**self.definition.params}

        for c, key in enumerate(self.definition.params.keys()):
            generic_args[key] = (params[c], func)

        def_copy = self.definition.copy()
        def_copy.is_generic = False
        def_copy.original_name = name_var
        def_copy.typ_name = new_name
        def_copy.params = generic_args

        # new_ty = Alias(self.module, name_var, def_copy.aliased, def_copy)
        # def_copy.typ = new_ty

        self.versions[params] = (def_copy.typ, generic_args, def_copy, pos)

        self.definition.fullfill_templates(self.module)

        return def_copy.typ

    def __getattribute__(self, name):
        self_members = (*Alias.__slots__, "set_type", "__init__", "__str__",
                        "__hash__", "declare", "dealias", "pass_type_params")
        if name in self_members:
            return object.__getattribute__(self, name)
        if hasattr(self.aliased_typ, name):
            return getattr(self.aliased_typ, name)

    def dealias(self):
        if isinstance(self.aliased_typ, Alias):
            return self.aliased_typ.dealias()
        return self.aliased_typ

    def declare(self, mod):
        '''Ensure declare works properly'''
        if self.dealias() in mod.declared_types:
            return

        if not self.is_generic:
            self.aliased_typ.declare(mod)
            return

        for ver in self.versions.values():
            ver[0].declare(mod)

    def __str__(self) -> str:
        return str(self.typ_name)

    def __hash__(self):
        return hash(self.typ_name + f".{self.module.location}")
