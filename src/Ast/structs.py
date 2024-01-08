import Ast.Ast_Types as Ast_Types
import errors
from Ast.Ast_Types.Type_Void import Void
from Ast.directives.directivenode import DirectiveList
from Ast.functions.definition import FunctionDef
from Ast.generics import GenericSpecify
from Ast.module import NamespaceInfo
from Ast.nodes import ASTNode, KeyValuePair
from Ast.nodes.commontypes import SrcPosition
from Ast.nodes.container import ContainerNode
from Ast.variables.reference import VariableRef
from Ast.variables.varobject import VariableObj


class StructDef(ASTNode):
    __slots__ = ("struct_name", "block", "struct_type", "block", "module",
                 "is_generic", "generic_args", "raw_name")

    can_have_modifiers = True

    def __init__(self, pos: SrcPosition, name, block, module,
                 register=True):
        super().__init__(pos)
        self.raw_name = name
        if isinstance(name, GenericSpecify):
            self.is_generic = True
            # (typ, func_of_origin)
            self.generic_args = {x.var_name: (Void(), None) for x in name.params}
            self.struct_name = name.left.var_name
            name.in_definition = True
        elif isinstance(name, VariableRef):
            self.is_generic = False
            self.generic_args = {}
            self.struct_name = name.var_name
        else:
            errors.error(f"Invalid type name: {name}",
                         line=name.position, full_line=True)

        if self.struct_name in Ast_Types.types_dict.keys():
            errors.error(f"Type name already in use: {self.struct_name}",
                         line=name.position, full_line=True)

        self.block = block
        self.block.parent = self
        members = []
        if isinstance(self.block.children[0], ContainerNode):
            members = self.block.children[0].children
        elif isinstance(self.block.children[0], KeyValuePair):
            members = [self.block.children[0]]
        else:
            errors.error("The first statement in a struct definition MUST " +
                         "be a list of members", line=self.block.children[0].pos)

        if register:
            self.struct_type = Ast_Types.Struct(self.struct_name, members, module, self.is_generic, self)
            module.types[self.struct_name] = self.struct_type
        module.add_struct_to_schedule(self)
        self.module = module
        # if self.is_generic:
        #     module.add_template_to_schedule(self)

    def copy(self):
        out = StructDef(self._position, self.raw_name.copy(),
                        self.block.copy(), self.module, register=False)
        out.modifiers = self.modifiers
        out.block.parent = out
        return out

    @property
    def ir_type(self):
        return self.struct_type.ir_type

    def get_type(self, _):
        return self.struct_type

    def get_type_by_name(self, var_name, pos):
        if var_name in self.generic_args.keys():
            return NamespaceInfo(self.generic_args[var_name][0], {})
        elif var_name == "Self":
            return NamespaceInfo(self.struct_type(), {})

        return self.module.get_type_by_name(var_name, pos)

    def get_unique_name(self, name: str) -> str:
        types = []
        for typ in self.generic_args.values():
            types.append(str(typ))

        return self.module.get_unique_name(f"__meth.{self.struct_name}.{name}.<{', '.join(types)}>")

    def validate_variable_exists(self, var_name, module=None):
        if var_name in self.generic_args.keys():
            return self.get_variable(var_name, module)
        elif var_name == "Self":
            return self.struct_type
        elif module is not None:
            value = module.get_global(var_name)
            if value is None:
                return None
            return value.obj

    def get_variable(self, var_name, module=None):
        '''Methods use this to get the names of types
        '''
        if var_name in self.generic_args.keys():
            var = self.generic_args[var_name][0]
            return var
        elif var_name == "Self":
            return self.struct_type
        elif module is not None:
            value = module.get_global(var_name)
            if value is None:
                return None
            return value.obj

    def _yield_functions(self):
        # skip first element
        for statement in self.block.children[1:]:
            statement = self._unwrap_directive(statement)

            if statement is None:
                continue

            if isinstance(statement, FunctionDef):
                yield statement
            else:
                errors.error("Struct bodies can only contain function " +
                             "declarations or member declarations",
                             line=statement.position)

    def create_function(self, name: str, func_obj):
        self.struct_type.create_function(name, func_obj)

    def scheduled(self, mod):
        self.struct_type.set_visibility(self.visibility)
        self.fullfill_templates(mod)

    def reset(self):
        self.block.reset()

    def _unwrap_directive(self, directive):
        '''if something is a directive, keep going thru it until reaching original node'''
        if not isinstance(directive, DirectiveList):
            return directive

        if isinstance(directive.statement, DirectiveList) and directive.should_compile:
            return self._unwrap_directive(directive.statement)

        if directive.should_compile:
            return directive.statement

    def fullfill_templates(self, func):
        if not self.is_generic:
            for stmt in self.block:
                stmt = self._unwrap_directive(stmt)

                if stmt is None:
                    continue

                if isinstance(stmt, FunctionDef):
                    stmt.parent = self
                stmt.fullfill_templates(self)

        for version in self.struct_type.versions.values():
            errors.templating_stack.append(version[3])
            version[2].fullfill_templates(version[2])
            del errors.templating_stack[-1]

    def post_parse(self, module):
        if not self.is_generic:
            self.struct_type.define(self)

        for version in self.struct_type.versions.values():
            errors.templating_stack.append(version[3])
            version[2].post_parse(version[2])
            del errors.templating_stack[-1]

        if self.is_generic:
            return

        for stmt in self._yield_functions():
            stmt.parent = self
            stmt.post_parse(self)

    def pre_eval(self, module):
        for version in self.struct_type.versions.values():
            errors.templating_stack.append(version[3])
            version[2].pre_eval(version[2])
            del errors.templating_stack[-1]

        if self.is_generic:
            return
        for stmt in self._yield_functions():
            stmt.pre_eval(self)

    def eval_impl(self, module):
        for version in self.struct_type.versions.values():
            errors.templating_stack.append(version[3])
            version[2].eval(version[2])
            del errors.templating_stack[-1]

        if self.is_generic:
            return

        for stmt in self._yield_functions():
            stmt.eval(self)

    def repr_as_tree(self) -> str:
        return self.create_tree("Struct Def Statement",
                                name=self.struct_name,
                                contents=self.block)
