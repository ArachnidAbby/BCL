import parser  # type: ignore

from llvmlite import binding, ir  # type: ignore

import Ast.functions.standardfunctions
import errors
import linker
from Ast.functions.functionobject import _Function
from Ast.nodes import ASTNode, SrcPosition
from lexer import Lexer

modules: dict[str, "Module"] = {}


class Module(ASTNode):
    __slots__ = ('location', 'functions', 'globals', 'imports', 'children',
                 'module', 'mod_name', 'target', 'parsed', 'pre_evaled',
                 'evaled', 'ir_saved', 'types')

    def __init__(self, pos: SrcPosition, name, location, tokens):
        super().__init__(pos)
        self.mod_name = name
        self.location = location
        # will be a dict of dicts: dict[str, dict[tuple, _Function]],
        # example: `{func_name: {arg_type_tuple: _Function(...)}}`
        self.functions: dict[str, dict[tuple, _Function]] = {}
        # TODO: object is a placeholder for when this feature is properly added
        self.globals: dict[str, object] = {}
        self.imports: dict[str, "Module"] = {}
        self.types: dict[str, "Type"] = {}   # type: ignore
        self.module = ir.Module(name=self.mod_name)
        self.module.triple = binding.get_default_triple()
        self.target = binding.Target.from_triple(self.module.triple)
        self.children = tokens
        self.parsed = False
        self.pre_evaled = False
        self.evaled = False
        self.ir_saved = False
        # Ast.functions.standardfunctions.declare_all(self.module)

        modules[name] = self

    def parse(self):
        pg = parser.Parser(self.children, self)
        self.children = pg.parse()
        self.parsed = True
        for imp in self.imports.values():
            if not imp.parsed:
                imp.parse()

    def add_import(self, file: str, name: str):
        if name in modules.keys():
            self.imports[name] = modules[name]
            return

        with open(file, 'r') as f:
            src_str = f.read()
            tokens = Lexer().get_lexer().lex(src_str)
            new_module = Ast.module.Module(SrcPosition.invalid(), name,
                                           file, tokens)
            self.imports[name] = new_module

    def create_type(self, name: str, typeobj: Ast.Type):
        self.types[name] = typeobj

    def get_type(self, name, position) -> Ast.Ast_Types.Type:  # type: ignore
        if name in self.types.keys():
            return self.types[name]
        for imp in self.imports.values():
            if name in imp.types.keys():
                return imp.types[name]
        if name in Ast.Ast_Types.definedtypes.types_dict.keys():
            return Ast.Ast_Types.definedtypes.types_dict[name]   # type: ignore

        errors.error(f"Cannot find type '{name}' in module" +
                     f"'{self.mod_name}'", line=position)

    def get_unique_name(self, name: str):
        return self.module.get_unique_name(name)

    def get_local_name(self, name: str, position: tuple[int, int, int]):
        '''get a local object by name, this could be a global, import,
        or function'''
        if name in self.globals:
            return self.globals[name]

        if name in self.functions:
            return self.functions[name]

        if name in self.imports:
            return self.imports[name]

        errors.error(f"Cannot find '{name}' in module '{self.mod_name}'",
                     line=position)

    def get_global(self, name: str, position: tuple[int, int, int]):
        '''get a global/constant'''
        if name in self.globals:
            return self.globals[name]

        errors.error(f"Cannot find global '{name}' in module" +
                     f"'{self.mod_name}'", line=position)

    def get_func_from_dict(self, name: str, funcs: dict, types: tuple, position):
        if types in funcs.keys():
            return funcs[types]

        # Iterate thru all functions with non-static args
        for func in funcs["NONSTATIC"]:
            if func.check_args_match(types):
                return func

        args_for_error = ','.join([str(x) for x in types])
        errors.error(f"function '{name}({args_for_error})'" +
                     "was never defined", line=position)

    def get_function(self, name: str, position: tuple[int, int, int]):
        '''get a function defined in module'''
        if name in self.functions.keys():
            return self.functions[name]
        for imp in self.imports.values():
            if name in imp.functions.keys():
                return imp.functions[name]

        errors.error(f"Cannot find function '{name}' in module" +
                     f" '{self.mod_name}'", line=position)

    def create_function(self, name: str, args_types: tuple,
                        function_object: _Function, dynamic: bool):
        if dynamic:  # TODO: This likely shouldn't be here
            self. create_dynamic_function(name, args_types, function_object)

        if name not in self.functions.keys():
            self.functions[name] = {args_types: function_object,
                                    "NONSTATIC": []}
            return
        self.functions[name][args_types] = function_object

    def create_dynamic_function(self, name: str, args_types: tuple,
                                function_object: _Function):
        if name not in self.functions.keys():
            self.functions[name] = {"NONSTATIC": [function_object]}
            return
        self.functions[name]["NONSTATIC"].append(function_object)

    def get_all_functions(self) -> list[_Function]:
        '''get all functions for linking'''
        output: list[_Function] = []
        for func_named in self.functions.values():
            output += func_named.values()
        return output

    def get_import_functions(self):
        output = []
        for mod in self.imports.values():
            output += mod.get_all_functions()
        return output

    def pre_eval(self):
        self.pre_evaled = True
        for mod in self.imports.values():
            if not mod.pre_evaled:
                mod.pre_eval()
                mod.pre_evaled = True

        for c, child in enumerate(self.children):
            if not child.completed:
                self.syntax_error_information(child, c)
            child.value.pre_eval()

    def eval(self):
        self.evaled = True
        for mod in self.imports.values():
            if not mod.evaled:
                mod.eval()
                mod.evaled = True

        for child in self.children:
            child.value.eval()

        # del self.children

    def repr_as_tree(self) -> str:
        return self.create_tree(f"Module {self.mod_name}",
                                functions=self.functions,
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
        funcs = self.get_import_functions()
        for func in funcs:
            if isinstance(func, list):
                for actual_func in func:
                    actual_func.declare(self)
                continue
            func.declare(self)
        if args["--emit-ast"]:
            print(self.repr_as_tree())
        llir = str(self.module)
        mod = binding.parse_assembly(llir)
        module_pass.run(mod)

        with open(f"{loc}/{self.mod_name}.ll", 'w') as output_file:
            output_file.write(str(mod))

        if not (args["--emit-object"] or args["--emit-binary"]):
            return
        with open(f"{loc}/{self.mod_name}.o", 'wb') as output_file:
            output_file.write(target.emit_object(mod))
        self.ir_saved = True

        other_args = args.copy()
        other_args["--emit-binary"] = False
        other_args["--emit-object"] = True
        objects = [f"{loc}/{self.mod_name}.o"]
        for mod in self.imports.values():
            mod.save_ir(f"{loc}/", other_args)
            objects.append(f"{loc}/{mod.mod_name}.o")

        if args["--emit-binary"]:
            extra_args = [f"-l{x}" for x in args["--libs"]]
            linker.link_all(f"{loc}/output", objects, extra_args)

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
