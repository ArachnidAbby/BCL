from typing import Protocol

from llvmlite import ir  # type: ignore

import errors
from Ast import Ast_Types
from Ast.nodes import (ASTNode, Block, ExpressionNode, KeyValuePair,
                       ParenthBlock)
from Ast.nodes.commontypes import SrcPosition
from Ast.variables.reference import VariableRef
from Ast.variables.varobject import VariableObj


class Parent(Protocol):
    ''' A protocol to define the necessary functionality
    for something to be considered a function parent
    '''

    def get_unique_name(self, name: str):
        pass

    def create_function(self, name: str, function_obj):
        pass

    @property
    def ir_type(self):
        #* optional
        pass

    def get_type(self):
        pass


class FunctionDef(ASTNode):
    '''Defines a function in the IR'''
    __slots__ = ('builder', 'block', 'function_ir', 'args', 'args_ir',
                 'module', 'is_ret_set', 'args_types', 'ret_type',
                 "has_return", "inside_loop", "func_name", "variables",
                 "ir_entry", "contains_dynamic", "contains_ellipsis",
                 "is_method", "raw_args")

    def __init__(self, pos: SrcPosition, name: str, args: ParenthBlock,
                 block: Block, module):
        self._position = pos
        self.func_name = name
        self.ret_type: Ast_Types.Type = Ast_Types.Void()

        self.builder = None   # llvmlite.ir.IRBuilder object once created
        self.block = block  # body of the function Ast.Block
        self.module = module  # Module the object is contained in
        self.is_ret_set = False  # is the return value set?
        # Not to be confused with "is_ret_set",
        # this is used for ensuring that a `return` always accessible
        self.has_return = False
        # Whether or not the IRBuilder is currently inside a loop block,
        # set to the loop node
        self.inside_loop = None
        # Entry section of the function. Used when declaring
        # "invisible" variables
        self.ir_entry = None
        self.variables: list[tuple] = []
        # ellipsis always make this dynamic
        self.contains_ellipsis = args.contains_ellipsis
        self.contains_dynamic = self.contains_ellipsis
        self.is_method = False

        self._validate_args(args)  # validate arguments

        # construct args lists
        self.raw_args = args
        self.args: dict[str, ExpressionNode] = dict()
        # list of all the args' ir types
        self.args_ir: tuple[ir.Type, ...] = ()
        # list of all the args' Ast_Types.Type return types
        self.args_types: tuple[Ast_Types.Type, ...] = ()

    def _construct_args(self, args: ParenthBlock, parent):
        '''Construct the lists of args required when building this function'''
        args_ir = []
        args_types = []
        if self.is_method:
            args.children[0] = KeyValuePair(args.children[0]._position, args.children[0], parent.get_type(self))
        for arg in args:
            self.args[arg.key.var_name] = \
                [None, arg.get_type(self), True]  # type: ignore
            if arg.get_type(self).pass_as_ptr:
                args_ir.append(arg.get_type(self).ir_type.as_pointer())
            else:
                args_ir.append(arg.get_type(self).ir_type)
            args_types.append(arg.get_type(self))
            if arg.get_type(self).is_dynamic:
                self.contains_dynamic = True

        self.args_ir = tuple(args_ir)
        self.args_types = tuple(args_types)

    def _validate_args(self, args: ParenthBlock):
        '''Validate that all args are syntactically valid'''
        for c, arg in enumerate(args):
            if not isinstance(arg, KeyValuePair) and c != 0:
                errors.error(f"Function {self.func_name}'s argument tuple " +
                             "consists of non KV_pairs", line=self.position)
            elif isinstance(arg, VariableRef) and c == 0:
                self.is_method = True

    def _validate_return(self, func):
        ret_line = SrcPosition.invalid()
        if self.is_ret_set:
            ret_line = self.ret_type.position
            self.ret_type = self.ret_type.as_type_reference(self)
        if (not self.ret_type.returnable) and self.block is not None:
            errors.error(f"Function {self.func_name} cannot return a " +
                         "reference to a local variable or value.",
                         line=ret_line)

    def _mangle_name(self, name, parent: Parent) -> str:
        '''add an ID to the end of a name if the function has a body and
        is NOT named "main"'''
        return parent.get_unique_name(name)

    def _append_args(self):
        '''append all args as variables usable inside the function body'''
        args = self.function_ir.args
        for c, x in enumerate(self.args.keys()):
            orig = self.args[x]
            var = VariableObj(orig[0], orig[1], True)
            self.block.variables[x] = var
            self.block.variables[x].ptr = args[c]
            self.variables.append((self.block.variables[x], x))

    def validate_variable_exists(self, var_name, module=None):
        if var_name in self.args.keys():
            return self.get_variable(var_name, module)
        elif module is not None:
            return module.get_global(var_name)

    def get_variable(self, var_name, module=None):
        ''' when the block is a child of this node,
        this function is used to find arguments as variables
        '''
        if var_name in self.args.keys():
            orig = self.args[var_name]
            var = VariableObj(orig[0], orig[1], True)
            return var
        elif module is not None:
            return module.get_global(var_name)

    def post_parse(self, parent: Parent):
        if self.block is not None:
            self.block.parent = self
        self._validate_return(self)
        self._construct_args(self.raw_args, parent)

        fnty = ir.FunctionType((self.ret_type).ir_type, self.args_ir,
                               self.contains_ellipsis)

        self.function_ir = ir.Function(self.module.module, fnty,
                                       name=self._mangle_name(self.func_name,
                                                              parent))
        function_object = Ast_Types.Function(self.func_name, self.args_types,
                                             self.function_ir, self.module)
        function_object.add_return(self.ret_type) \
                       .set_ellipses(self.contains_ellipsis) \
                       .set_method(self.is_method, parent)

        parent.create_function(self.func_name, function_object)

    def pre_eval(self, parent: Parent):
        # Early return if the function has no body.
        if self.has_no_body:
            return

        block = self.function_ir.append_basic_block("entry")
        self.builder = ir.IRBuilder(block)
        self.ir_entry = block
        self.block.pre_eval(self)
        self._append_args()

    def create_const_var(self, typ):
        current_block = self.builder.block
        self.builder.position_at_start(self.ir_entry)
        ptr = self.builder.alloca(typ.ir_type, name="CONST")
        self.builder.position_at_end(current_block)
        return ptr

    def alloc_stack(self):
        # TODO: REFACTOR
        for x in self.variables:
            if x[0].is_constant:
                if x[0].type.pass_as_ptr:
                    val = self.builder.load(x[0].ptr)
                else:
                    val = x[0].ptr
                if not x[0].type.no_load:
                    ptr = self.builder.alloca(x[0].type.ir_type)
                    self.builder.store(val, ptr)
                    x[0].ptr = ptr
                x[0].is_constant = False
                continue
            else:
                x[0].define(self, x[1])

    def eval(self, parent):
        if self.has_no_body:
            return
        self.function_ir.attributes.add("nounwind")
        # self.block.pre_eval(self)
        self.alloc_stack()

        self.block.eval(self)

        if self.ret_type.is_void():
            self.builder.ret_void()
        elif not self.has_return:
            errors.error(f"Function '{self.func_name}' has no guaranteed " +
                         "return! Ensure that at least 1 return statement is" +
                         " reachable!")

    @property
    def has_no_body(self) -> bool:
        return self.block is None

    def repr_as_tree(self) -> str:
        return self.create_tree("Function Definition",
                                name=self.func_name,
                                contents=self.block,
                                return_type=self.ret_type)
