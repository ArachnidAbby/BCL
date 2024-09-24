import os
import parser  # type: ignore
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, Optional, Self, Union

from llvmlite import binding, ir  # type: ignore
from rply import LexingError
from typing_extensions import Protocol

import Ast
import errors
import linker
from Ast import Ast_Types, package
from Ast.nodes import ASTNode, Modifiers, SrcPosition
from Ast.package import Package
from Ast.variables.reference import VariableRef
from lexer import Lexer

modules: dict[str, "Module"] = {}
base_package: Package | None = None
alt_packages = []  # alternative search paths available everywhere

STDLIB_PATH = Path(os.path.dirname(__file__)) / "../libbcl"


def make_base_package(path: Path, cmd_args: dict,
                      alt_search_paths=[STDLIB_PATH]):
    global base_package, alt_packages
    base_package = package.get_all_packages(path, cmd_args)
    for loc in alt_search_paths:
        pkg = package.get_all_packages(loc, cmd_args)
        alt_packages.append(pkg)
    errors.developer_info(base_package)


def create_target_dirs(base_dir: str):
    if os.path.exists(f"{base_dir}/target/ll"):
        return

    os.makedirs(f"{base_dir}/target/ll")

    if os.path.exists(f"{base_dir}/target/o"):
        return

    os.makedirs(f"{base_dir}/target/o")


# Can be used as a namespace to pull things from.
class Namespace(Protocol):
    def get_namespace_name(self, func, name, pos,
                           stack=None,
                           override_star=False) -> Optional["NamespaceInfo"]:
        pass

    def get_type_by_name(self, name, position, stack=None,
                         override_star=False) -> Optional["NamespaceInfo"]:
        pass

    def get_global(self, name: str, pos=SrcPosition.invalid(),
                   stack=None, override_star=False) -> Optional["NamespaceInfo"]:
        pass


@dataclass
class NamespaceInfo():
    obj: Namespace
    imported_names: dict[str, Self]
    using_namespace: bool = False
    is_public: bool = False

    def get_namespace_name(self, func, name, pos,
                           stack=None,
                           override_star=False) -> Optional["NamespaceInfo"]:
        if stack is None:
            stack = []

        override_star = override_star | self.using_namespace | True
        first_try = self.obj.get_namespace_name(func, name, pos, stack=stack,
                                                override_star=override_star)
        if first_try is not None:
            return first_try
        if name not in self.imported_names:
            # print("FAILED TO FIND", name)
            return None

        value = self.imported_names[name]
        if not override_star and not value.using_namespace:
            # print("FAILED TO FIND (bad import)", name)
            return None
        return value

    def get_type_by_name(self, name, position, stack=None,
                         override_star=False) -> Optional["NamespaceInfo"]:
        if stack is None:
            stack = []
        override_star = override_star | self.using_namespace
        first_try = self.obj.get_type_by_name(name, position, stack=stack,
                                              override_star=override_star)
        if first_try is not None:
            return first_try

        value = None

        for imp in self.imported_names.values():
            second_try = imp.get_type_by_name(name, position, stack=stack,
                                              override_star=override_star)
            if second_try is not None:
                value = second_try
                break

        if value is None:
            # print("FAILED TO FIND", name)
            return None

        # value = self.imported_names[name]
        if not override_star and not value.using_namespace:
            # print("FAILED TO FIND (bad import)", name)
            return None
        return value

    def get_global(self, name: str, pos=SrcPosition.invalid(),
                   stack=None, override_star=False) -> Optional["NamespaceInfo"]:
        if stack is None:
            stack = []
        override_star = override_star | self.using_namespace | True
        first_try = self.obj.get_global(name, pos=pos, stack=stack,
                                        override_star=override_star)
        if first_try is not None:
            return first_try

        value = None

        for imp in self.imported_names.values():
            second_try = imp.get_global(name, pos=pos, stack=stack,
                                        override_star=override_star)
            if second_try is not None:
                value = second_try
                break

        if value is None:
            # print("FAILED TO FIND", name)
            return None

        # # value = self.imported_names[name]
        # if not override_star and not value.using_namespace:
        #     # print("FAILED TO FIND (bad import)", name)
        #     return None
        return value

    @classmethod
    def make_from_namespace(cls, base: Package, namespace_index, is_public=False) -> Self:
        '''namespace_index essentially is a linked list.
        We return a reversed version.
        so `a::b::c` => (c->b->a)
        => (a->b->c)'''
        from Ast.namespace import NamespaceIndex
        if isinstance(namespace_index, VariableRef):
            name = namespace_index.var_name.strip()
            if name not in base.modules.keys():
                # errors.error(f"Could not find module: {errors.RESET}'{name}'{errors.RED}",
                #              line=namespace_index.position)
                #              note=f"Known modules: \n{errors.RESET}\t" + f"\n{errors.RESET}\t".join(base.modules.keys()))
                return None

            module = base.modules[namespace_index.var_name]
            return NamespaceInfo(module, {}, is_public=is_public)
        right = namespace_index.resolve_import(base)
        thing = NamespaceInfo(right, {},
                              using_namespace=namespace_index.star_idx,
                              is_public=is_public)
        if right is None:
            return None
            # errors.error(f"Could not find specified name during import",
            #              line=namespace_index.position)

        if isinstance(namespace_index.left, NamespaceIndex):
            left = NamespaceInfo.make_from_namespace(base, namespace_index.left)
            if namespace_index.right == "*" or namespace_index.left == "..":
                return thing
            left.imported_names[namespace_index.right] = thing
            return left

        if namespace_index.right == "*" or namespace_index.left == "..":
            return thing
        lhs = base.get_namespace_name(None, namespace_index.left.var_name,
                                      namespace_index.left.position)

        left = NamespaceInfo(lhs, {})
        left.imported_names[namespace_index.right] = thing

        return left


def _get_name(pkg_or_mod):
    if isinstance(pkg_or_mod, NamespaceInfo):
        pkg_or_mod = pkg_or_mod.obj

    if isinstance(pkg_or_mod, Package):
        return pkg_or_mod.pkg_name
    return pkg_or_mod.mod_name


def combine_import_tree(imp_tree, linked_list: NamespaceInfo):
    if linked_list.obj is None:
        return
    if isinstance(imp_tree, dict):
        name = _get_name(linked_list.obj)
        if name not in imp_tree.keys():
            imp_tree[name] = linked_list
            return
        for val in linked_list.imported_names.values():
            combine_import_tree(imp_tree[name], val)
    elif isinstance(imp_tree, NamespaceInfo):  # ? is this silly stuff necessary? idk.
        name = _get_name(linked_list.obj)
        if name not in imp_tree.imported_names.keys():
            imp_tree.imported_names[name] = linked_list
            return
        for val in linked_list.imported_names.values():
            combine_import_tree(imp_tree.imported_names[name], val)


class Module(ASTNode):
    __slots__ = ('location', 'globals', 'imports', 'children',
                 'module', 'mod_name', 'target', 'parsed', 'pre_evaled',
                 'evaled', 'ir_saved', 'types', 'post_parsed',
                 'scheduled_events', 'ran_schedule', 'target_machine',
                 'scheduled_templates', 'cmd_args', 'declared_types',
                 'package', 'imported_modules')

    is_namespace = True
    ENUM_SCHEDULE_ID = 0
    STRUCT_SCHEDULE_ID = 1
    TEMPLATE_SCHEDULE_ID = 2
    ALIAS_SCHEDULE_ID = 3

    def __init__(self, pos: SrcPosition, name, location, tokens,
                 cmd_args: dict):
        super().__init__(pos)
        self.mod_name = name
        self.location = location
        self.package = None # the package this module is included in
        self.globals: dict[str, object] = {}
        self.imports: dict[str, NamespaceInfo] = {}
        self.imported_modules: list["Module"] = [] # any modules we import.
        self.types: dict[str, "Type"] = {}   # type: ignore
        self.module = ir.Module(name=self.mod_name)
        self.module.triple = binding.get_default_triple()
        self.cmd_args = cmd_args
        if cmd_args["--debug"]:
            di_file = self.module.add_debug_info(
                "DIFile",
                {
                    "filename": self.mod_name+".bcl",
                    "directory": self.location
                }
            )
            # self.module.add_debug_info(
            #     "DICompileUnit",
            #     {
            #         "language": ir.DIToken("DW_LANG_BCL"),
            #         "file": di_file,
            #         "producer": "PyBCL Compiler (v0.7.0-alpha)",
            #         "runtimeVersion": 0,
            #         "isOptimized": True,
            #     },
            #     is_distinct=True
            # )
        self.target = binding.Target.from_triple(self.module.triple)
        self.target_machine = self.target.create_target_machine(force_elf=True,
                                                        codemodel="default")
        self.children = tokens
        self.parsed = False
        self.pre_evaled = False
        self.post_parsed = False
        self.evaled = False
        self.ir_saved = False
        self.scheduled_events = [[], [], [], []]
        self.scheduled_templates = []
        self.declared_types = []  # types that have had their .declare method ran.
        self.ran_schedule = False

        modules[name] = self

    def parse(self):
        pg = parser.Parser(self.children, self)
        self.children = pg.parse()
        self.parsed = True
        for imp in self.imported_modules:
            if isinstance(imp, NamespaceInfo):
                imp = imp.obj
            if not imp.parsed:
                try:
                    imp.parse()
                except LexingError as e:
                    error_pos = e.source_pos
                    pos = SrcPosition(error_pos.lineno, error_pos.colno, 0,
                                      str(imp.location))
                    errors.error("A Lexing Error has occured. Invalid Syntax",
                                 line=pos, full_line=True)

    def add_enum_to_schedule(self, enum_def):
        self.scheduled_events[self.ENUM_SCHEDULE_ID].append(enum_def)

    def add_struct_to_schedule(self, struct_def):
        self.scheduled_events[self.STRUCT_SCHEDULE_ID].append(struct_def)

    def add_alias_to_schedule(self, alias_def):
        self.scheduled_events[self.ALIAS_SCHEDULE_ID].append(alias_def)

    def add_template_to_schedule(self, generic):
        self.scheduled_templates.append(generic)

    def remove_scheduled(self, node):
        for bucket in self.scheduled_events:
            for c, event in enumerate(bucket):
                if event is node:
                    bucket.pop(c)
                    break

    def do_scheduled(self):
        if self.ran_schedule:
            return

        for bucket in self.scheduled_events:
            for event in bucket:
                event.scheduled(self)

        self.ran_schedule = True

        for imp in self.imported_modules:
            if isinstance(imp, NamespaceInfo):
                imp = imp.obj
            imp.do_scheduled()

    def get_namespace_name(self, func, name, pos,
                           stack=None, override_star=False) -> Optional[NamespaceInfo]:
        '''Getting a name from the namespace'''
        if name in self.types.keys():
            t = self.types[name]
            if t.visibility == Modifiers.VISIBILITY_PRIVATE \
                    and func.module.location != self.location:
                errors.error("Type is private", line=pos)
            return NamespaceInfo(t, {})
        elif name in self.globals.keys():
            return NamespaceInfo(self.globals[name], {})

        private_imports = False

        if stack is None:
            stack = [self]
        else:
            private_imports = True
            stack.append(self)

        note = "Note:\n" + \
               f"{errors.CODE81}Import statements currently cannot import " + \
               f"types or\n{errors.CODE81}function names declared in a module." + \
               f"\n{errors.CODE81}Those names are not intitialized at this stage"

        base_imports = self._get_base_imports()
        for imp, mod in zip(base_imports.keys(), base_imports.values()):
            if not mod.is_public and not private_imports:
                note = "Note: It is a private import!"
                continue
            elif imp == name:
                return mod
            elif mod.obj in stack:
                continue
            elif mod.using_namespace:
                return mod.obj.get_namespace_name(func, name, pos, stack,
                                                  override_star)

        errors.error(f"Name \"{name}\" cannot be " +
                     f"found in module \"{stack[0].mod_name}\"",
                     line=pos,
                     note=note)

    def register_namespace(self, func, obj, name):
        errors.error(f"Cannot register namespace {name}")

    def add_import(self, namespace, using_namespace, is_public=False,
                   relative_import=True):

        base = self.package if relative_import else base_package

        linked_list = NamespaceInfo.make_from_namespace(base, namespace, is_public)
        if linked_list is None:
            for pkg in alt_packages:
                linked_list = NamespaceInfo.make_from_namespace(pkg, namespace, is_public)
                if linked_list is not None:
                    break

        if linked_list is None:
            errors.error("Could not find specified name during import",
                         line=namespace.position)

        combine_import_tree(self.imports, linked_list)
        imported = None

        if isinstance(namespace, VariableRef):
            if namespace.var_name in base.modules.keys():
                imported = base.modules[namespace.var_name]
            else:
                for pkg in alt_packages:
                    if namespace.var_name not in pkg.modules.keys():
                        continue
                    imported = pkg.modules[namespace.var_name]
                    break
        else:
            imported = namespace.resolve_import(base)
            if imported is None:
                for pkg in alt_packages:
                    imported = namespace.resolve_import(pkg)
                    if imported is not None:
                        imported = imported.obj
                        break
            else:
                imported = imported.obj

        if imported is None:
            errors.error("Could not find specified name during import",
                         line=namespace.position)

        if isinstance(imported, Package):
            errors.error("Cannot import a package directly.",
                         line=namespace.position)
        self.imported_modules.append(imported)

    def create_type(self, name: str, typeobj: Ast.Type):
        self.types[name] = typeobj
        self.declared_types.append(typeobj) # no need to run declare.

    # ! Probably unncessary
    def _get_base_imports(self):
        return self.imports

    def get_type_by_name(self, name, position, stack=None,
                         override_star=False) -> Optional[NamespaceInfo]:
        not_top_level = False

        if stack is None:
            stack = [self]
        else:
            if self in stack:
                return
            not_top_level = True
            stack.append(self)

        if name in self.types.keys():
            typ = self.types[name]
            if (not_top_level) and typ.visibility == Modifiers.VISIBILITY_PRIVATE:
                errors.error(f"Type is private (From module, {self.mod_name})", # TODO
                             line=position)
            return NamespaceInfo(typ, {})

        for imp in self._get_base_imports().values():
            if not imp.using_namespace:
                continue
            if not_top_level and not imp.is_public:
                continue
            typ = imp.get_type_by_name(name, position, stack=stack,
                                       override_star=override_star | imp.using_namespace)
            if typ is not None:
                return typ

        if name in Ast.Ast_Types.definedtypes.types_dict.keys():
            return NamespaceInfo(Ast.Ast_Types.definedtypes.types_dict[name], {})

    def get_unique_name(self, name: str):
        if name == "main":  # ! main is special because of runtime stuff.
            return name

        pkg_made_name = self.package.get_unique_name(f"{self.mod_name}.{name}")
        return self.module.get_unique_name(pkg_made_name)

    def get_global(self, name: str, pos=SrcPosition.invalid(),
                   stack=None, override_star=False) -> Optional[NamespaceInfo]:
        '''get a global/constant'''
        if name in self.globals:
            return NamespaceInfo(self.globals[name], {})
        if name in self.types:
            t = self.types[name]
            if t.visibility == Modifiers.VISIBILITY_PRIVATE \
                    and stack is not None:
                errors.error("Type is private", line=pos)
            return NamespaceInfo(t, {})

        if name in self.imports.keys():
            return self.imports[name]

        private_imports = False
        if stack is None:
            stack = [self]
        else:
            if self in stack:
                return
            private_imports = True
            stack.append(self)

        for imp in self.imports.values():
            if not imp.using_namespace:
                continue
            if imp.obj in stack:
                continue
            if private_imports and not imp.is_public:
                continue
            if (gbl := imp.get_global(name, pos, stack, override_star)) is not None:
                return gbl

        if name in Ast.Ast_Types.definedtypes.types_dict.keys():
            return NamespaceInfo(Ast.Ast_Types.definedtypes.types_dict[name], {})

    def get_func_from_dict(self, name: str, funcs: dict, types: tuple,
                           position):
        if types in funcs.keys():
            return funcs[types]

        # Iterate thru all functions with non-static args
        for func in funcs["NONSTATIC"]:
            if func.check_args_match(types):
                return func

        args_for_error = ','.join([str(x) for x in types])
        errors.error(f"function '{name}({args_for_error})'" +
                     "was never defined", line=position)

    def create_function(self, name: str, function_object: Ast_Types.Function):
        if name not in self.globals.keys():
            self.globals[name] = Ast_Types.FunctionGroup(name, self)
        group = self.globals[name]
        group.add_function(function_object)  # type: ignore
        return group

    def copy(self):
        return self

    def __eq__(self, other):
        return isinstance(other, Module) and self.location == other.location

    def post_parse(self, parent):
        self.post_parsed = True
        for mod in self.imported_modules:
            if isinstance(mod, NamespaceInfo):
                mod = mod.obj
            if not mod.post_parsed:
                mod.post_parse(mod)
                mod.post_parsed = True

        for child in reversed(self.children):
            if child.name == "EOF":
                self.children.pop(-1)

        for c, child in enumerate(self.children):
            if not child.completed:
                self.syntax_error_information(child, c)
            child.value.post_parse(self)

    def fullfill_templates(self, stack=None):
        if stack is None:
            stack = [self]
        else:
            if self in stack:
                return
            stack.append(self)

        for mod in self.imported_modules:
            if isinstance(mod, NamespaceInfo):
                mod = mod.obj
            mod.fullfill_templates(stack=stack)

        for child in reversed(self.children):
            if child.name == "EOF":
                self.children.pop(-1)

        for c, child in enumerate(self.children):
            if not child.completed:
                self.syntax_error_information(child, c)
            child.value.fullfill_templates(self)

    def pre_eval(self, parent):
        self.pre_evaled = True
        for mod in self.imported_modules:
            if isinstance(mod, NamespaceInfo):
                mod = mod.obj
            if not mod.pre_evaled:
                mod.pre_eval(mod)
                mod.pre_evaled = True

        for c, child in enumerate(self.children):
            child.value.pre_eval(self)

    def eval_impl(self, parent):
        self.evaled = True
        for mod in self.imported_modules:
            if isinstance(mod, NamespaceInfo):
                mod = mod.obj
            if not mod.evaled:
                mod.eval(mod)
                mod.evaled = True

        for child in self.children:
            child.value.eval(self)

    def repr_as_tree(self) -> str:
        return self.create_tree(f"Module {self.mod_name}",
                                globals=self.globals,
                                location=self.location,
                                contents=[x.value for x in self.children])

    def get_all_types(self, stack=None):
        if stack is None:
            stack = [self]
        elif self in stack:
            return []
        else:
            stack.append(self)

        output = [(self, typ) for typ in self.types.values()]
        for mod in self.imported_modules:
            if isinstance(mod, NamespaceInfo):
                mod = mod.obj
            output += mod.get_all_types(stack=stack)
        return output

    def get_all_globals(self, stack=None):
        if stack is None:
            stack = [self]
        elif self in stack:
            return []
        else:
            stack.append(self)

        output = [(self, glbl) for glbl in self.globals.values()]
        for mod in self.imported_modules:
            if isinstance(mod, NamespaceInfo):
                mod = mod.obj
            output += mod.get_all_globals(stack=stack)
        return output

    def save_ir(self, loc, args={}, stack=None):
        if self.ir_saved:
            return []

        if stack is None:
            stack = [self]
        elif self in stack:
            return []
        else:
            stack.append(self)

        target = self.target_machine

        module_pass = binding.ModulePassManager()
        # * commented out optimizations may be re-added later on
        # pass_manager = binding.PassManagerBuilder()
        # pass_manager.loop_vectorize = True
        # pass_manager.opt_level = 1
        module_pass.add_memcpy_optimization_pass()
        module_pass.add_reassociate_expressions_pass()
        module_pass.add_aggressive_instruction_combining_pass()
        module_pass.add_dead_code_elimination_pass()
        # module_pass.add_instruction_combining_pass()
        # module_pass.add_arg_promotion_pass() # not available in LLVM>14
        # module_pass.add_sink_pass()
        module_pass.add_constant_merge_pass()
        module_pass.add_dead_store_elimination_pass()
        # module_pass.add_cfg_simplification_pass() # completely breaks shit (94% memory usage type beat)
        # module_pass.add_merge_returns_pass()
        # pass_manager.populate(module_pass)

        for mod, typ in self.get_all_types():
            if mod is self:
                continue
            self.declared_types.append(typ)
            typ.declare(self)

        for mod, glbl in self.get_all_globals():
            if mod == self:
                continue
            glbl.declare(self)

        if args["--emit-ast"]:
            print(self.repr_as_tree())

        llir = str(self.module)
        # mod = llir
        mod = binding.parse_assembly(llir)
        module_pass.run(mod)
        create_target_dirs(loc)

        mangled_name = self.package.get_unique_name(self.mod_name)

        with open(f"{loc}/target/ll/{mangled_name}.ll", 'w') as output_file:
            output_file.write(str(mod))

        if not (args["--emit-object"] or args["--emit-binary"]):
            return
        with open(f"{loc}/target/o/{mangled_name}.o", 'wb') as output_file:
            output_file.write(target.emit_object(mod))
        self.ir_saved = True

        other_args = args.copy()
        other_args["--emit-binary"] = False
        other_args["--emit-object"] = True
        other_args["--run"] = False
        objects = [f"{loc}/target/o/{mangled_name}.o"]

        # using global list of modules
        for mod in self.imported_modules:
            if isinstance(mod, NamespaceInfo):
                mod = mod.obj
            mod.declare_builtins()
            other_objs = mod.save_ir(f"{loc}", other_args)
            for obj in other_objs:
                if obj in objects:
                    continue
                objects.append(obj)

        if args["--emit-binary"]:
            extra_args = [f"-l{x}" for x in args["--libs"]]
            return linker.link_all(f"{loc}/target/output", objects, extra_args)
        return objects

    def declare_builtins(self):
        if self.ir_saved:
            return

        for typ in Ast.Ast_Types.definedtypes.needs_declare:
            typ.declare(self)

    # TODO: Create a seperate error parser
    def syntax_error_information(self, child, c: int):
        '''more useful syntax error messages'''
        errors.developer_info(f'item: {child}   in: {self.children}')

        if child.name == "CLOSED_SQUARE" and self.children[c+1].completed:
            errors.error("""
            Unclosed square brackets
            """.strip(), line=child.pos)

        reached_semicolon = False
        last_pos = SrcPosition.invalid()
        for err in self.children[c:]:
            if err.name == "CLOSE_CURLY":
                break
            if err.name == "SEMI_COLON":
                reached_semicolon = True
            if err.pos != SrcPosition.invalid():
                last_pos = err.pos

        if not reached_semicolon:
            errors.error("""
            Missing semicolon
            """.strip(), line=last_pos, full_line=True)

        errors.error("""
        Syntax error or compiler bug. If you have questions, ask on the
        github issues page.
        (or use '--dev' when compiling to see the remaining tokens)
        """.strip(), line=child.pos, full_line=True)
