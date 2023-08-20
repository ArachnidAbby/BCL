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
    def is_iterator(self):
        return self.aliased_typ.is_iterator

    @property
    def returnable(self):
        return self.aliased_typ.returnable

    @property
    def ir_type(self):
        return self.aliased_typ.ir_type

    @property
    def is_method(self):
        return self.aliased_typ.is_method

    @property
    def needs_dispose(self):
        return self.aliased_typ.needs_dispose

    @property
    def is_generic(self):
        return self.aliased_typ.is_generic

    @property
    def generate_bounds_check(self):
        return self.aliased_typ.generate_bounds_check

    @property
    def has_members(self):
        return self.aliased_typ.has_members

    @property
    def read_only(self):
        return self.aliased_typ.read_only

    @property
    def no_load(self):
        return self.aliased_typ.no_load

    @property
    def rang(self):
        return self.aliased_typ.rang

    @property
    def check_lifetime(self):
        return self.aliased_typ.check_lifetime

    @property
    def pass_as_ptr(self):
        return self.aliased_typ.pass_as_ptr

    @property
    def literal_index(self):
        return self.aliased_typ.literal_index

    def __str__(self) -> str:
        return self.typ_name

    def __hash__(self):
        return hash(self.typ_name)
