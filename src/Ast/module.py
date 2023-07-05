import os
from typing import NamedTuple
import parser  # type: ignore

from llvmlite import binding, ir  # type: ignore

import Ast.functions.standardfunctions
import errors
import linker
from Ast import Ast_Types
from Ast.nodes import ASTNode, SrcPosition
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


class Module(ASTNode):
    __slots__ = ('location', 'globals', 'imports', 'children',
                 'module', 'mod_name', 'target', 'parsed', 'pre_evaled',
                 'evaled', 'ir_saved', 'types', 'post_parsed',
                 'scheduled_events', 'ran_schedule')

    is_namespace = True
    ENUM_SCHEDULE_ID = 0

    def __init__(self, pos: SrcPosition, name, location, tokens):
        super().__init__(pos)
        self.mod_name = name
        self.location = location
        self.globals: dict[str, object] = {}
        self.imports: dict[str, NamespaceInfo] = {}
        self.types: dict[str, "Type"] = {}   # type: ignore
        self.module = ir.Module(name=self.mod_name)
        self.module.triple = binding.get_default_triple()
        self.target = binding.Target.from_triple(self.module.triple)
        self.children = tokens
        self.parsed = False
        self.pre_evaled = False
        self.post_parsed = False
        self.evaled = False
        self.ir_saved = False
        self.scheduled_events = [[], [], []]
        self.ran_schedule = False

        modules[name] = self

    def parse(self):
        pg = parser.Parser(self.children, self)
        self.children = pg.parse()
        self.parsed = True
        for imp in self.imports.values():
            if not imp.obj.parsed:
                imp.obj.parse()

    def add_enum_to_schedule(self, enum_def):
        self.scheduled_events[self.ENUM_SCHEDULE_ID].append(enum_def)

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

    def get_namespace_name(self, func, name, pos):
        '''Getting a name from the namespace'''
        if name in self.types.keys():
            return self.types[name]
        elif name in self.globals.keys():
            return self.globals[name]
        for imp, mod in zip(self.imports.keys(), self.imports.values()):
            if imp == name:
                return mod.obj
            elif mod.using_namespace:
                return mod.obj.get_namespace_name(func, name, pos)

        errors.error(f"Name \"{name}\" cannot be " +
                     f"found in module \"{self.mod_name}\"",
                     line=pos)

    def register_namespace(self, func, obj, name):
        errors.error(f"Cannot register namespace {name}")

    def add_import(self, file: str, name: str, using_namespace: bool):
        if name in modules.keys():
            self.imports[name] = NamespaceInfo(modules[name], using_namespace)
            return

        with open(file, 'r') as f:
            src_str = f.read()
            tokens = Lexer().get_lexer().lex(src_str)
            new_module = Ast.module.Module(SrcPosition.invalid(), name,
                                           file, tokens)
            self.imports[name] = NamespaceInfo(new_module, using_namespace)

    def create_type(self, name: str, typeobj: Ast.Type):
        self.types[name] = typeobj

    def get_type(self, name, position) -> Ast.Ast_Types.Type:  # type: ignore
        if name in self.types.keys():
            return self.types[name]
        for imp in self.imports.values():
            if not imp.using_namespace:
                continue
            if name in imp.obj.types.keys():
                return imp.obj.types[name]
        if name in Ast.Ast_Types.definedtypes.types_dict.keys():
            return Ast.Ast_Types.definedtypes.types_dict[name]   # type: ignore

        errors.error(f"Cannot find type '{name}' in module " +
                     f"'{self.mod_name}'", line=position)

    def get_unique_name(self, name: str):
        return self.module.get_unique_name(name)

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

    def get_global(self, name: str, pos=SrcPosition.invalid(), stack=None) -> object | None:
        '''get a global/constant'''
        if name in self.globals:
            return self.globals[name]
        if name in self.types:
            return self.types[name]

        # imp instead of "import"
        # gbl instead of "global"
        if name in self.imports.keys():
            return self.imports[name].obj

        if stack is None:
            stack = [self]
        else:
            stack.append(self)

        for imp in self.imports.values():
            if not imp.using_namespace:
                continue
            if imp.obj in stack:
                continue
            if (gbl := imp.obj.get_global(name, pos, stack=stack)) is not None:
                return gbl

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

    def get_all_globals(self) -> list[object]:
        '''get all functions for linking'''
        output: list[object] = []
        for func in self.globals.values():
            output.append(func)
        return output

    def get_import_globals(self):
        output = []
        for mod in self.imports.values():
            output += mod.obj.get_all_globals()
        return output

    def get_all_types(self) -> list[object]:
        '''get all functions for linking'''
        output: list[object] = []
        for typ in self.types.values():
            output.append(typ)
        return output

    def get_import_types(self):
        output = []
        for mod in self.imports.values():
            output += mod.obj.get_all_types()
        return output

    def post_parse(self, parent):
        self.post_parsed = True
        for mod in self.imports.values():
            if not mod.obj.post_parsed:
                mod.obj.post_parse(mod)
                mod.obj.post_parsed = True

        for c, child in enumerate(self.children):
            if not child.completed:
                self.syntax_error_information(child, c)
            child.value.post_parse(self)

    def pre_eval(self, parent):
        self.pre_evaled = True
        for mod in self.imports.values():
            if not mod.obj.pre_evaled:
                mod.obj.pre_eval(mod)
                mod.obj.pre_evaled = True

        for c, child in enumerate(self.children):
            child.value.pre_eval(self)

    def eval(self, parent):
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
        target = self.target.create_target_machine(force_elf=True,
                                                   codemodel="default")
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
        funcs = self.get_import_globals()
        for func in funcs:
            func.declare(self)
        types = self.get_import_types()
        for typ in types:
            typ.declare(self)
        if args["--emit-ast"]:
            print(self.repr_as_tree())
        llir = str(self.module)
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
        objects = [f"{loc}/target/o/{self.mod_name}.o"]
        for mod in self.imports.values():
            mod.obj.save_ir(f"{loc}", other_args)
            objects.append(f"{loc}/target/o/{mod.obj.mod_name}.o")

        if args["--emit-binary"]:
            extra_args = [f"-l{x}" for x in args["--libs"]] + ['-lm']  # adds math.h
            linker.link_all(f"{loc}/target/output", objects, extra_args)

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
