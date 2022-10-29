import errors
from llvmlite import binding, ir

from Ast.nodes import ASTNode

global_functions = {} #! this will likely be later deprecated once `import <name>` is added

class Module(ASTNode):
    __slots__ = ('name', 'location', 'functions', 'globals', 'imports', 'children', 'module')

    def init(self, name, location):
        self.name      = name
        self.location  = location
        self.functions = dict() # will be a dict of dicts: dict[str, dict[tuple, _Function]], example: `{func_name: {arg_type_tuple: _Function(...)}}`
        self.globals   = dict()
        self.imports   = dict()

        self.children  = list()
    
    def add_child(self, item):
        self.children.append(item)

    def get_local_name(self, name: str, position : tuple[int, int, int]):
        '''get a local object by name, this could be a global, import, or function'''
        if name in self.globals:
            return self.globals[name]
        
        elif name in self.functions:
            return self.functions[name]
        
        elif name in self.imports:
            return self.imports[name]
        
        else:
            errors.error(f"Cannot find '{name}' in module '{self.name}'", line = position)

    def get_global(self, name: str, position: tuple[int, int, int]):
        '''get a global/constant'''
        if name in self.globals:
            return self.globals[name]
        
        errors.error(f"Cannot find global '{name}' in module '{self.name}'", line = position)
    
    def get_function(self, name: str, position: tuple[int, int, int]):
        '''get a function defined in module'''
        if name in self.functions:
            return self.functions[name]
        
        errors.error(f"Cannot find function '{name}' in module '{self.name}'", line = position)

    def pre_eval(self):

        self.module = ir.Module(name=self.name)
        self.module.triple = binding.get_default_triple()

        for child in self.children:
            if not child.completed:
                print(child)
                errors.error(f"""
                The compiler could not complete all it's operations.

                Note: this is an error the compiler was not designed to catch.
                    If you encounter this, send all relavent information to language devs.
                """, line = child.pos)
                

            child.value.pre_eval()

    def eval(self):
        for child in self.children:
            child.value.eval(self)
    
