from Ast.Node_Types import NodeTypes
import Errors
from llvmlite import ir

from .Nodes import AST_NODE, Block, ParenthBlock
from .Ast_Types.Utils import Types

functions = {}
func_calls = []

class FunctionDef(AST_NODE):
    '''Defines a function in the IR'''
    __slots__ = ('builder', 'block', 'function_ir', 'args', 'args_ir', 'module','is_ret_set', 'args_types')
    
    def init(self, name: str, args: ParenthBlock, block: Block, module):
        self.name = name
        self.type = NodeTypes.STATEMENT
        self.ret_type = Types.VOID

        self.builder = None
        self.block = block
        self.module = module
        self.is_ret_set = False

        if not args.is_key_value_pairs():
            Errors.error(f"Function {self.name}'s argument tuple consists of non KV_pairs", line = self.position)
        for x in args.children:
            if not x.keywords:
                Errors.error(f"Function {self.name}'s argument tuple can only consist of Keyword pairs\n\t invalid pair \
                    '{x.key}: {x.value}'", line = self.position)
        
        self.args = {x.key: [None, x.value, True] for x in args.children}
        self.args_ir = tuple([(Types[x.validate_type()].value).ir_type for x in args.children])  # type: ignore
        self.args_types = tuple([Types[x.validate_type()] for x in args.children])

    def pre_eval(self):
        fnty = ir.FunctionType((self.ret_type.value).ir_type, self.args_ir, False)

        self.function_ir = ir.Function(self.module, fnty, name=self.name)
        
        global functions
        if self.name not in functions:
            functions[self.name] = dict()
        
        functions[self.name][self.args_types] = [self.function_ir, self.ret_type]

    def eval(self):
        self.block.pre_eval()
        block = self.function_ir.append_basic_block("entry")
        self.builder = ir.IRBuilder(block)

        args = self.function_ir.args
        
        # * add variables into block
        for c,x in enumerate(self.args.keys()):
            self.block.variables[x].ptr = args[c]
        
        self.block.eval(self)
        
        if self.ret_type == Types.VOID:
            self.builder.ret_void()

class ReturnStatement(AST_NODE):
    __slots__ = ('expr')

    def init(self, expr):
        self.name = "return"
        self.type = NodeTypes.STATEMENT
        self.ret_type = Types.VOID
        self.expr = expr

    def pre_eval(self):
        pass

    def eval(self, func):
        self.expr.pre_eval()
        if self.expr.ret_type != func.ret_type:
            Errors.error(
                f"Funtion, \"{func.name}\", has a return type of '{func.ret_type}'. Return statement returned '{self.expr.ret_type}'",
                line = self.position
            )

        if func.ret_type == Types.VOID:
            func.builder.ret_void()
            return None

        func.builder.ret(self.expr.eval(func))
class FunctionCall(AST_NODE):
    '''Defines a function in the IR'''
    __slots__ = ('ir_type', 'paren', 'function', 'args_types')
    
    def init(self, name: str, parenth: ParenthBlock):
        self.name = name
        self.type = NodeTypes.EXPRESSION
        self.ret_type = Types.UNKNOWN
        self.ir_type = None

        self.paren = parenth
    
    def pre_eval(self):
        self.paren.pre_eval()

        self.args_types = tuple([x.ret_type for x in self.paren.children])
        if self.name not in functions or self.args_types not in functions[self.name]:
            Errors.error(f"function '{self.name}{self.args_types}' was never defined", line = self.position)

        self.ret_type = functions[self.name][self.args_types][1]
        self.ir_type = (self.ret_type.value).ir_type
        self.function = functions[self.name][self.args_types][0]
    
    def eval(self, func):
        x = self.paren.eval(func)
        args = self.paren.children if x==None else [x]
        
        return func.builder.call(self.function, args)
