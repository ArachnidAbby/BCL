from llvmlite import ir

from .Nodes import AST_NODE, Block, ParenthBlock
from .Types import types
import Errors

functions = {}
func_calls = []

def process_func_call():
    '''deprecated'''
    # print(functions)
    # print(func_calls)
    for func in func_calls:
        name = func.name

class FunctionDef(AST_NODE):
    '''Defines a function in the IR'''
    __slots__ = ['builder', 'block', 'function_ir', 'args']
    
    def init(self, name: str, args: ParenthBlock, block: Block, module):
        self.name = name
        self.type = "Function"
        self.ret_type = "void"

        self.builder = None
        self.block = block

        if not args.is_key_value_pairs():
            Errors.error(f"Function {self.name}'s argument tuple consists of non KV_pairs")
        
        self.args = {x.key: [None, x.value, True] for x in args.children}
        print(self.args)
        print([types[x.value].ir_type for x in args.children])

        fnty = ir.FunctionType(ir.VoidType(), tuple([types[x.value].ir_type for x in args.children]), False)

        self.function_ir = ir.Function(module, fnty, name=self.name)
        

        # print("FUNCIN")
        global functions
        functions[name] = [self.function_ir, self.ret_type]
        # print(functions)
    
    def eval(self):
        block = self.function_ir.append_basic_block("entry")
        self.builder = ir.IRBuilder(block)

        global functions
        functions[self.name] = [self.function_ir, self.ret_type]

        args = self.function_ir.args
        print(self.block.children)
        # print(args)
        for c,x in enumerate(self.args.keys()):
            self.block.variables[x][0] = args[c]

        self.block.pre_eval()

        for instr in self.block.children:  # type: ignore
            instr.eval(self)
        
        if self.ret_type == "void":
            self.builder.ret_void()

class FunctionCall(AST_NODE):
    '''Defines a function in the IR'''
    __slots__ = ['function_ir', 'paren', 'function']
    
    def init(self, name: str, parenth: AST_NODE):
        self.name = name
        self.type = "FunctionCall"
        self.ret_type = 'unknown'

        # global func_calls
        # func_calls.append(self)

        self.paren = parenth
    
    def pre_eval(self):
        self.ret_type = functions[self.name][1]
        self.function = functions[self.name][0]
    
    def eval(self, func):
        
        self.paren.pre_eval()

        x = self.paren.eval(func)
        args = self.paren.children if x==None else [x]
        
        # print(functions[self.name], args)
        
        return func.builder.call(self.function, args)