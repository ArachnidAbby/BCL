import parser

import errors
from llvmlite import binding, ir

from Ast.nodes import ASTNode

global_functions = {} #! this will likely be later deprecated once `import <name>` is added

class Module(ASTNode):
    __slots__ = ('location', 'functions', 'globals', 'imports', 'children', 'module', 'mod_name')

    def init(self, name, location, tokens):
        self.mod_name      = name
        self.location  = location
        self.functions = {} # will be a dict of dicts: dict[str, dict[tuple, _Function]], example: `{func_name: {arg_type_tuple: _Function(...)}}`
        self.globals   = {}
        self.imports   = {}
        self.module = ir.Module(name=self.mod_name)
        self.module.triple = binding.get_default_triple()

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

    def save_ir(self, loc):
        with open(loc, 'w') as output_file:
            output_file.write(str(self.module))

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
