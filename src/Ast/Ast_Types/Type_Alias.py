from Ast.Ast_Types.Type_Base import Type

# from Ast.nodes.commontypes import SrcPosition


class Alias(Type):
    __slots__ = ('module', 'aliased_typ', 'name',
                 'typ_name', 'is_public')

    def __init__(self, module, name, aliased):
        self.aliased_typ = aliased
        self.typ_name = name
        self.name = ""
        self.module = module
        self.is_public = False

    def set_type(self, typ, public):
        self.aliased_typ = typ
        self.name = typ.name
        self.is_public = public

    def __getattr__(self, name):
        return getattr(self.aliased_typ, name)

    @property
    def ir_type(self):
        return self.aliased_typ.ir_type

    @property
    def pass_as_ptr(self):
        return self.aliased_typ.pass_as_ptr

    @property
    def no_load(self):
        return self.aliased_typ.no_load

    @property
    def read_only(self):
        return self.aliased_typ.read_only

    @property
    def has_members(self):
        return self.aliased_typ.has_members

    @property
    def returnable(self):
        return self.aliased_typ.returnable

    @property
    def checks_lifetime(self):
        return self.aliased_typ.checks_lifetime

    @property
    def is_dynamic(self):
        return self.aliased_typ.is_dynamic

    @property
    def functions(self):
        return self.aliased_typ.functions

    @property
    def is_iterator(self):
        return self.aliased_typ.is_iterator

    @property
    def is_method(self):
        return self.aliased_typ.is_method

    @property
    def literal_index(self):
        return self.aliased_typ.literal_index

    @property
    def is_namespace(self):
        return self.aliased_typ.is_namespace

    @property
    def needs_dispose(self):
        return self.aliased_typ.needs_dispose

    @property
    def is_generic(self):
        return self.aliased_typ.is_generic

    @property
    def ref_counted(self):
        return self.aliased_typ.ref_counted

    @property
    def generate_bounds_check(self):
        return self.aliased_typ.generate_bounds_check

    @property
    def rang(self):
        return self.aliased_typ.rang

    def __str__(self) -> str:
        return self.typ_name

    def __hash__(self):
        return hash(self.typ_name)
