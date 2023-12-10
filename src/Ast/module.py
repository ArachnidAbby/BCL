import os
import parser  # type: ignore
from typing import NamedTuple

from llvmlite import binding, ir  # type: ignore
from rply import LexingError

import Ast.functions.standardfunctions
import errors
import linker
from Ast import Ast_Types
from Ast.nodes import ASTNode, Modifiers, SrcPosition
from lexer import Lexer

modules: dict[str, "Module"] = {}


def create_target_dirs(base_dir: str):
    if os.path.exists(f"{base_dir}/target/ll"):
        return

    os.makedirs(f"{base_dir}/target/ll")

    if os.path.exists(f"{base_dir}/target/o"):
        return

    os.makedirs(f"{base_dir}/target/o")


class NamespaceInfo(NamedTuple):
    obj: "Module"
    using_namespace: bool = False
    is_public: bool = False


class Module(ASTNode):
    __slots__ = ('location', 'globals', 'imports', 'children',
                 'module', 'mod_name', 'target', 'parsed', 'pre_evaled',
                 'evaled', 'ir_saved', 'types', 'post_parsed',
                 'scheduled_events', 'ran_schedule', 'target_machine',
                 'scheduled_templates', 'cmd_args', 'declared_types')

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
        self.globals: dict[str, object] = {}
        self.imports: dict[str, NamespaceInfo] = {}
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
        self.declared_types = [] # types that have had their .declare method ran.
        self.ran_schedule = False

        modules[name] = self

    def parse(self):
        pg = parser.Parser(self.children, self)
        self.children = pg.parse()
        self.parsed = True
        for imp in self.imports.values():
            if not imp.obj.parsed:
                try:
                    imp.obj.parse()
                except LexingError as e:
                    error_pos = e.source_pos
                    pos = SrcPosition(error_pos.lineno, error_pos.colno, 0, str(imp.obj.location))
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

        for imp in self.imports.values():
            if not imp.obj.ran_schedule:
                imp.obj.do_scheduled()

    def get_namespace_name(self, func, name, pos, stack=None):
        '''Getting a name from the namespace'''
        if name in self.types.keys():
            t = self.types[name]
            if t.visibility == Modifiers.VISIBILITY_PRIVATE \
                    and func.module.location != self.location:
                errors.error("Type is private", line=pos)
            return t
        elif name in self.globals.keys():
            return self.globals[name]

        private_imports = False

        if stack is None:
            stack = [self]
        else:
            private_imports = True
            stack.append(self)

        for imp, mod in zip(self.imports.keys(), self.imports.values()):
            if imp == name:
                return mod.obj
            elif mod.obj in stack:
                continue
            elif not mod.is_public and private_imports:
                continue
            elif mod.using_namespace:
                return mod.obj.get_namespace_name(func, name, pos, stack)

        errors.error(f"Name \"{name}\" cannot be " +
                     f"found in module \"{stack[0].mod_name}\"",
                     line=pos)

    def register_namespace(self, func, obj, name):
        errors.error(f"Cannot register namespace {name}")

    def add_import(self, file: str, name: str, using_namespace: bool,
                   is_public=False):
        if name in modules.keys():
            self.imports[name] = NamespaceInfo(modules[name], using_namespace, is_public)
            return

        with open(file, 'r') as f:
            src_str = f.read()
            tokens = Lexer().get_lexer().lex(src_str)
            new_module = Ast.module.Module(SrcPosition.invalid(), name,
                                           file, tokens, self.cmd_args)
            self.imports[name] = NamespaceInfo(new_module, using_namespace, is_public)

    def create_type(self, name: str, typeobj: Ast.Type):
        self.types[name] = typeobj
        self.declared_types.append(typeobj) # no need to run declare.

    def get_type_by_name(self, name, position, stack=None) -> Ast.Ast_Types.Type:  # type: ignore
        private_imports = False
        if stack is None:
            stack = [self]
        else:
            if self in stack:
                return
            private_imports = True
            stack.append(self)

        if name in self.types.keys():
            typ = self.types[name]
            if (private_imports) and typ.visibility == Modifiers.VISIBILITY_PRIVATE:
                errors.error(f"Type is private (From module, {self.mod_name})",
                             line=position)
            return typ

        for imp in self.imports.values():
            if not imp.using_namespace:
                continue
            if private_imports and not imp.is_public:
                continue
            typ = imp.obj.get_type_by_name(name, position, stack=stack)
            if typ is not None:
                return typ

        if name in Ast.Ast_Types.definedtypes.types_dict.keys():
            return Ast.Ast_Types.definedtypes.types_dict[name]   # type: ignore

        if private_imports:
            return

        errors.error(f"Cannot find type '{name}' in module " +
                     f"'{self.mod_name}'", line=position)

    def get_unique_name(self, name: str):
        if name == "main":  #! main is special because of the crt.
            return name
        # ! Using names alone could get messy in the future. Change this when packages are added.
        return self.module.get_unique_name(f"{self.mod_name}.{name}")

    def get_local_name(self, name: str, position: tuple[int, int, int]):
        '''get a local object by name, this could be a global, import,
        or function'''
        if name in self.globals:
            return self.globals[name]
        if name in self.types:
            return self.types[name]

        if name in self.imports:
            return self.imports[name]

        errors.error(f"Cannot find '{name}' in module '{self.mod_name}'",
                     line=position)

    def get_global(self, name: str, pos=SrcPosition.invalid(),
                   stack=None) -> object | None:
        '''get a global/constant'''
        if name in self.globals:
            return self.globals[name]
        if name in self.types:
            t = self.types[name]
            if t.visibility == Modifiers.VISIBILITY_PRIVATE \
                    and stack is not None:
                errors.error("Type is private", line=pos)
            return t

        # imp instead of "import"
        # gbl instead of "global"
        if name in self.imports.keys():
            return self.imports[name].obj

        private_imports = False
        if stack is None:
            stack = [self]
        else:
            private_imports = True
            stack.append(self)

        for imp in self.imports.values():
            if not imp.using_namespace:
                continue
            if imp.obj in stack:
                continue
            if private_imports and not imp.is_public:
                continue
            if (gbl := imp.obj.get_global(name, pos, stack=stack)) is not None:
                return gbl

        if name in Ast.Ast_Types.definedtypes.types_dict.keys():
            return Ast.Ast_Types.definedtypes.types_dict[name]   # type: ignore

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

    def get_import_globals(self):
        output = []
        for mod in self.imports.values():
            output += mod.obj.get_all_globals(stack=[self])
        return output

    def post_parse(self, parent):
        self.post_parsed = True
        for mod in self.imports.values():
            if not mod.obj.post_parsed:
                mod.obj.post_parse(mod)
                mod.obj.post_parsed = True

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

        for mod in self.imports.values():
            mod.obj.fullfill_templates(stack=stack)

        for child in reversed(self.children):
            if child.name == "EOF":
                self.children.pop(-1)

        for c, child in enumerate(self.children):
            if not child.completed:
                self.syntax_error_information(child, c)
            child.value.fullfill_templates(self)

    def pre_eval(self, parent):
        self.pre_evaled = True
        for mod in self.imports.values():
            if not mod.obj.pre_evaled:
                mod.obj.pre_eval(mod)
                mod.obj.pre_evaled = True

        for c, child in enumerate(self.children):
            child.value.pre_eval(self)

    def eval_impl(self, parent):
        self.evaled = True
        for mod in self.imports.values():
            if not mod.obj.evaled:
                mod.obj.eval(mod)
                mod.obj.evaled = True

        for child in self.children:
            child.value.eval(self)

        # del self.children

    def repr_as_tree(self) -> str:
        return self.create_tree(f"Module {self.mod_name}",
                                globals=self.globals,
                                location=self.location,
                                contents=[x.value for x in self.children])

    def save_ir(self, loc, args={}):
        if self.ir_saved:
            return

        target = self.target_machine

        module_pass = binding.ModulePassManager()
        # * commented out optimizations may be re-added later on
        # pass_manager = binding.PassManagerBuilder()
        # pass_manager.loop_vectorize = True
        # pass_manager.opt_level = 1
        module_pass.add_memcpy_optimization_pass()
        module_pass.add_reassociate_expressions_pass()
        # module_pass.add_refprune_pass()
        module_pass.add_dead_code_elimination_pass()
        # module_pass.add_instruction_combining_pass()
        module_pass.add_arg_promotion_pass()
        # module_pass.add_sink_pass()
        module_pass.add_constant_merge_pass()
        # module_pass.add_dead_store_elimination_pass()
        module_pass.add_cfg_simplification_pass()
        # module_pass.add_merge_returns_pass()
        # pass_manager.populate(module_pass)

        for mod in modules.values():
            if mod == self:
                continue
            # declare all types originating from imports
            for typ in mod.types.values():
                self.declared_types.append(typ)
                typ.declare(self)
            # declare all functions originating from imports
            for func in mod.globals.values():
                func.declare(self)

        if args["--emit-ast"]:
            print(self.repr_as_tree())

        llir = str(self.module)
        # mod = llir
        mod = binding.parse_assembly(llir)
        module_pass.run(mod)
        create_target_dirs(loc)

        with open(f"{loc}/target/ll/{self.mod_name}.ll", 'w') as output_file:
            output_file.write(str(mod))

        if not (args["--emit-object"] or args["--emit-binary"]):
            return
        with open(f"{loc}/target/o/{self.mod_name}.o", 'wb') as output_file:
            output_file.write(target.emit_object(mod))
        self.ir_saved = True

        other_args = args.copy()
        other_args["--emit-binary"] = False
        other_args["--emit-object"] = True
        other_args["--run"] = False
        objects = [f"{loc}/target/o/{self.mod_name}.o"]

        # using global list of modules
        for mod in modules.values():
            if mod == self:
                continue
            mod.declare_builtins()
            mod.save_ir(f"{loc}", other_args)
            objects.append(f"{loc}/target/o/{mod.mod_name}.o")

        if args["--emit-binary"]:
            extra_args = [f"-l{x}" for x in args["--libs"]] + ['-lm']  # adds math.h
            linker.link_all(f"{loc}/target/output", objects, extra_args)

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
