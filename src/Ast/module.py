import parser

import errors
from llvmlite import binding, ir

from Ast.nodes import ASTNode

global_functions = {} #! this will likely be later deprecated once `import <name>` is added

class Module(ASTNode):
    __slots__ = ('location', 'functions', 'globals', 'imports', 'children', 'module', 'mod_name', 'target')

    def init(self, name, location, tokens):
        self.mod_name      = name
        self.location  = location
        self.functions = {} # will be a dict of dicts: dict[str, dict[tuple, _Function]], example: `{func_name: {arg_type_tuple: _Function(...)}}`
        self.globals   = {}
        self.imports   = {}
        self.module = ir.Module(name=self.mod_name)
        self.module.triple = binding.get_default_triple()
        self.target = binding.Target.from_triple(self.module.triple)

        self.children  = tokens

    def parse(self):
        pg = parser.Parser(self.children, self)
        self.children = pg.parse()
    
    def add_child(self, item):
        self.children.append(item)

    def get_local_name(self, name: str, position : tuple[int, int, int]):
        '''get a local object by name, this could be a global, import, or function'''
        if name in self.globals:
            return self.globals[name]

        if name in self.functions:
            return self.functions[name]

        if name in self.imports:
            return self.imports[name]

        errors.error(f"Cannot find '{name}' in module '{self.mod_name}'", line = position)

    def get_global(self, name: str, position: tuple[int, int, int]):
        '''get a global/constant'''
        if name in self.globals:
            return self.globals[name]
        
        errors.error(f"Cannot find global '{name}' in module '{self.mod_name}'", line = position)
    
    def get_function(self, name: str, position: tuple[int, int, int]):
        '''get a function defined in module'''
        if name in self.functions:
            return self.functions[name]
        
        errors.error(f"Cannot find function '{name}' in module '{self.mod_name}'", line = position)

    def pre_eval(self):
        for c, child in enumerate(self.children):
            if not child.completed:                    
                self.syntax_error_information(child, c)
            child.value.pre_eval()

    def eval(self):
        for child in self.children:
            child.value.eval()

    def save_ir(self, loc, create_object_file = False):
        target = self.target.create_target_machine()
        module_pass = binding.ModulePassManager()
        pass_manager = binding.PassManagerBuilder()
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
        
        llir = str(self.module)
        mod = binding.parse_assembly(llir)

        # pass_manager.populate(module_pass)
        module_pass.run(mod)

        with open(f"{loc}.ll", 'w') as output_file:
            output_file.write(str(mod))
        if not create_object_file:
            return
        with open(f"{loc}.o", 'wb') as output_file:            
            output_file.write(target.emit_object(mod))

    def syntax_error_information(self, child, c: int):
        '''more useful syntax error messages'''
        errors.developer_info(f'item: {child}   in: {self.children}')

        if child.name == "CLOSED_SQUARE" and self.children[c+1].completed:
            errors.error(f"""
            Unclosed square brackets
            """.strip(), line = child.pos)

        reached_semicolon = False
        last_pos = (-1,-1,-1)
        for err in self.children[c:]:
            if err.name=="CLOSE_CURLY":
                break
            if err.name == "SEMI_COLON":
                reached_semicolon = True
            if err.pos!= (-1,-1,-1): last_pos = err.pos
        
        if not reached_semicolon:
            errors.error(f"""
            Missing semicolon
            """.strip(), line = last_pos, full_line= True)
        
        errors.error(f"""
        Syntax error or compiler bug. If you have questions, ask on the github issues page.
        (or use '--dev' when compiling to see the remaining tokens)
        """.strip(), line = child.pos, full_line = True)
