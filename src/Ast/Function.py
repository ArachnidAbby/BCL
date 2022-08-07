from llvmlite import ir

from .Nodes import AST_NODE, Block, ParenthBlock
from .Types import types
import Errors

functions = {}
func_calls = []

class FunctionDef(AST_NODE):
    '''Defines a function in the IR'''
    __slots__ = ['builder', 'block', 'function_ir', 'args', 'args_ir', 'module','is_ret_set']
    
    def init(self, name: str, args: ParenthBlock, block: Block, module):
        self.name = name
        self.type = "Function"
        self.ret_type = "void"

        self.builder = None
        self.block = block
        self.module = module
        self.is_ret_set = False

        if not args.is_key_value_pairs():
            Errors.error(f"Function {self.name}'s argument tuple consists of non KV_pairs")
        
        self.args = {x.key: [None, x.value, True] for x in args.children}
        self.args_ir = tuple([types[x.value].ir_type for x in args.children])
        # print(self.args)
        # print([types[x.value].ir_type for x in args.children])

    def pre_eval(self):
        fnty = ir.FunctionType(types[self.ret_type].ir_type, self.args_ir, False)

        self.function_ir = ir.Function(self.module, fnty, name=self.name)
        
        global functions
        functions[self.name] = [self.function_ir, self.ret_type]
    
    def eval(self):
        block = self.function_ir.append_basic_block("entry")
        self.builder = ir.IRBuilder(block)

        global functions
        functions[self.name] = [self.function_ir, self.ret_type]

        args = self.function_ir.args
        
        for c,x in enumerate(self.args.keys()):
            self.block.variables[x][0] = args[c]

        self.block.pre_eval()

        for instr in self.block.children:  # type: ignore
            instr.eval(self)
        
        if self.ret_type == "void":
            self.builder.ret_void()

class ReturnStatement(AST_NODE):
    __slots__ = ['expr']

    def init(self, expr):
        self.name = "return"
        self.type = "Return Statement"
        self.ret_type = "void"
        self.expr = expr

    def pre_eval(self):
        pass

    def eval(self, func):
        if func.ret_type == "void":
            func.builder.ret_void()
            return None
        func.builder.ret(self.expr.eval(func))
class FunctionCall(AST_NODE):
    '''Defines a function in the IR'''
    __slots__ = ['ir_type', 'paren', 'function']
    
    def init(self, name: str, parenth: AST_NODE):
        self.name = name
        self.type = "FunctionCall"
        self.ret_type = 'unknown'
        self.ir_type = None

        # global func_calls
        # func_calls.append(self)

        self.paren = parenth
    
    def pre_eval(self):
        self.ret_type = functions[self.name][1]
        self.ir_type = types[self.ret_type].ir_type
        self.function = functions[self.name][0]
    
    def eval(self, func):
        
        self.paren.pre_eval()

        x = self.paren.eval(func)
        args = self.paren.children if x==None else [x]
        
        # print(functions[self.name], args)
        
        return func.builder.call(self.function, args)