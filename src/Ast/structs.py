import Ast.Ast_Types as Ast_Types
from Ast.generics import GenericSpecify
from Ast.variables.reference import VariableRef
from Ast.variables.varobject import VariableObj
import errors
from Ast.functions.definition import FunctionDef
from Ast.nodes import ASTNode, KeyValuePair
from Ast.nodes.commontypes import SrcPosition
from Ast.nodes.container import ContainerNode


class StructDef(ASTNode):
    __slots__ = ("struct_name", "block", "struct_type", "block", "module",
                 "is_generic", "generic_args")

    can_have_modifiers = True

    def __init__(self, pos: SrcPosition, name, block, module):
        super().__init__(pos)
        if isinstance(name.value, GenericSpecify):
            self.is_generic = True
            self.generic_args = {x.var_name: None for x in name.value.params}
            self.struct_name = name.value.left.var_name
        elif isinstance(name.value, VariableRef):
            self.is_generic = False
            self.generic_args = {}
            self.struct_name = name.value.var_name
        else:
            errors.error(f"Invalid type name: {name.value.var_name}",
                         line=name.pos, full_line=True)

        if self.struct_name in Ast_Types.types_dict.keys():
            errors.error(f"Type name already in use: {self.struct_name}",
                         line=name.pos, full_line=True)

        self.block = block
        members = []
        if isinstance(self.block.children[0], ContainerNode):
            members = self.block.children[0].children
        elif isinstance(self.block.children[0], KeyValuePair):
            members = [self.block.children[0]]
        else:
            errors.error("The first statement in a struct definition MUST " +
                         "be a list of members", line=self.block.children[0].pos)
        self.struct_type = Ast_Types.Struct(self.struct_name, members, module, self.is_generic, self)
        module.types[self.struct_name] = self.struct_type
        self.module = module
        module.add_struct_to_schedule(self)

    @property
    def ir_type(self):
        return self.struct_type.ir_type

    def get_type(self, _):
        return self.struct_type

    def get_type_by_name(self, var_name, pos):
        if var_name in self.generic_args.keys():
            return self.generic_args[var_name]

        return self.module.get_type_by_name(var_name, pos)

    def get_unique_name(self, name: str) -> str:
        types = []
        for typ in self.generic_args.values():
            types.append(str(typ))

        return self.module.get_unique_name(f"__meth.{self.struct_name}.{name}.<{', '.join(types)}>")

    def validate_variable_exists(self, var_name, module=None):
        if var_name in self.generic_args.keys():
            return self.get_variable(var_name, module)
        elif module is not None:
            return module.get_global(var_name)

    def get_variable(self, var_name, module=None):
        '''Methods use this to get the names of types
        '''
        if var_name in self.generic_args.keys():
            var = self.generic_args[var_name]
            return var
        elif module is not None:
            return module.get_global(var_name)

    def _yield_functions(self):
        # skip first element
        for statement in self.block.children[1:]:
            if isinstance(statement, FunctionDef):
                yield statement
            else:
                errors.error("Struct bodies can only contain function " +
                             "declarations or member declarations",
                             line=statement.pos)

    def create_function(self, name: str, func_obj):
        self.struct_type.create_function(name, func_obj)

    def scheduled(self, mod):
        self.struct_type.set_visibility(self.visibility)

    def post_parse(self, module):
        self.struct_type.define(self)

        if self.is_generic:
            return

        for stmt in self._yield_functions():
            # stmt.func_name = f"{stmt.func_name}"
            stmt.parent = self
            stmt.post_parse(self)

    def pre_eval(self, module):
        if self.is_generic:
            return
        for stmt in self._yield_functions():
            stmt.pre_eval(self)

    def eval_impl(self, module):
        if self.is_generic:
            return

        for stmt in self._yield_functions():
            stmt.eval(self)

    def repr_as_tree(self) -> str:
        return self.create_tree("Struct Def Statement",
                                name=self.struct_name,
                                contents=self.block)
