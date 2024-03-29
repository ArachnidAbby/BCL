import platform
from typing import Protocol

from llvmlite import ir

import errors
from Ast import Ast_Types
from Ast.Ast_Types.Type_Base import Type
from Ast.Ast_Types.Type_Void import Void
from Ast.functions.yieldstatement import YieldStatement
from Ast.nodes import (ASTNode, Block, ExpressionNode, KeyValuePair,
                       ParenthBlock)
from Ast.nodes.commontypes import Modifiers, SrcPosition
from Ast.nodes.passthrough import PassNode  # type: ignore
from Ast.reference import Ref
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

    def get_type_by_name(self):
        pass


class FunctionDef(ASTNode):
    '''Defines a function in the IR'''
    __slots__ = ('builder', 'block', 'function_ir', 'args', 'args_ir',
                 'module', 'is_ret_set', 'args_types', 'ret_type',
                 "has_return", "inside_loop", "func_name", "variables",
                 "ir_entry", "contains_dynamic", "contains_ellipsis",
                 "is_method", "raw_args", "yields", "yield_type",
                 "yield_struct_ptr", "yield_consts", "yield_function",
                 "yield_block", "yield_gen_type", "yield_after_blocks",
                 "yield_start", "dispose_queue", "parent", "ret_raw",
                 "function_ty", "lifetime_checked_nodes")

    can_have_modifiers = True

    def __init__(self, pos: SrcPosition, name: str, args: ParenthBlock,
                 block: Block, module):
        super().__init__(pos)
        self.func_name = name
        self.ret_type: Ast_Types.Type = Ast_Types.Void()
        self.ret_raw = Ast_Types.Void()
        self.builder = None   # llvmlite.ir.IRBuilder object once created
        self.block = block  # body of the function Ast.Block
        self.module = module  # Module the object is contained in
        self.parent = None
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

        # Whether or not the function contains a yield statement
        self.yields = False
        self.yield_type = None
        self.yield_gen_type = None
        self.yield_struct_ptr = None
        self.yield_function = None
        self.yield_block = None
        self.yield_start = None
        self.yield_after_blocks = []
        self.yield_consts = []

        self.dispose_queue = []

        self._validate_args(args)  # validate arguments

        # construct args lists
        self.raw_args = args
        self.args: dict[str, ExpressionNode] = dict()
        # list of all the args' ir types
        self.args_ir: tuple[ir.Type, ...] = ()
        # list of all the args' Ast_Types.Type return types
        self.args_types: tuple[Ast_Types.Type, ...] = ()
        self.lifetime_checked_nodes = []

    def copy(self):
        if self.block is not None:
            val = FunctionDef(self._position,
                              self.func_name, self.raw_args.copy(),
                              self.block.copy(), self.module)
            self.block.parent = val
        else:
            val = FunctionDef(self._position, self.func_name,
                              self.raw_args.copy(),
                              None, self.module)

        if not isinstance(self.ret_raw, Void):
            val.ret_raw = self.ret_raw.copy()
        val.modifiers = self.modifiers
        val.is_ret_set = self.is_ret_set
        return val

    def reset(self):
        super().reset()
        self.has_return = False
        self.yields = False
        self.yield_type = None
        self.yield_gen_type = None
        self.yield_struct_ptr = None
        self.yield_function = None
        self.yield_block = None
        self.yield_start = None
        self.builder = None
        self.parent = None
        self.yield_after_blocks = []
        self.yield_consts = []
        self.ir_entry = None
        self.variables = []

        self.ret_type = self.ret_raw

        self.dispose_queue = []
        self.args: dict[str, ExpressionNode] = dict()
        # list of all the args' ir types
        self.args_ir: tuple[ir.Type, ...] = ()
        # list of all the args' Ast_Types.Type return types
        self.args_types: tuple[Ast_Types.Type, ...] = ()
        self.block.reset()

    def get_unique_name(self, name: str) -> str:
        return self.module.get_unique_name(f"{self.func_name}.local.{name}")

    def get_type_by_name(self, var_name, pos):
        if self.parent is not None:
            return self.parent.get_type_by_name(var_name, pos)

        return self.module.get_type_by_name(var_name, pos)

    def create_function(self, name, function_obj):
        if name not in self.block.variables.keys():
            self.block.variables[name] = Ast_Types.FunctionGroup(name, self)
        group = self.block.variables[name]
        group.add_function(function_obj)  # type: ignore
        return group

    def add_method_arg(self, arg, parent) -> KeyValuePair:
        if isinstance(arg, VariableRef):
            return KeyValuePair(arg._position, arg, parent.get_type(self))

        if isinstance(arg, Ref) and isinstance(arg.var, VariableRef):
            return KeyValuePair(arg._position, arg.var,
                                Ast_Types.Reference(parent.get_type(self)))
        else:
            errors.error("Invalid syntax, first argument must be a " +
                         "Key-Value pair, Reference, or Variable name.",
                         line=arg.position)
            return  # type: ignore

    def register_dispose(self, node):
        self.dispose_queue.append(node)

    def _construct_args(self, args: ParenthBlock, parent):
        '''Construct the lists of args required when building this function'''
        args_ir = []
        args_types = []
        if self.is_method:
            old_arg_0 = args.children[0]
            args.children[0] = self.add_method_arg(args.children[0], parent)
        for idx, arg in enumerate(args):
            arg.ensure_unmodified()
            self.args[arg.key.var_name] = \
                [None, arg.get_type(self), True, idx]  # type: ignore
            if arg.get_type(self).pass_as_ptr:
                args_ir.append(arg.get_type(self).ir_type.as_pointer())
            else:
                args_ir.append(arg.get_type(self).ir_type)
            args_types.append(arg.get_type(self))
            if arg.get_type(self).is_dynamic:
                self.contains_dynamic = True

        if self.is_method:
            args.children[0] = old_arg_0

        self.args_ir = tuple(args_ir)
        self.args_types = tuple(args_types)

    def _validate_args(self, args: ParenthBlock):
        '''Validate that all args are syntactically valid'''
        for c, arg in enumerate(args):
            if not isinstance(arg, KeyValuePair) and c != 0:
                errors.error(f"Function {self.func_name}'s argument tuple " +
                             "consists of non KV_pairs", line=self.position)
            elif isinstance(arg, VariableRef):
                self.is_method = True
            elif isinstance(arg, Ref) and isinstance(arg.var, VariableRef):
                self.is_method = True

    def _validate_return(self, func):
        ret_line = SrcPosition.invalid()
        if self.is_ret_set:
            ret_line = self.ret_raw.position
            self.ret_type = self.ret_raw.as_type_reference(self)
        # if (not self.ret_type.returnable) and self.block is not None:
        #     errors.error(f"Function {self.func_name} cannot return a " +
        #                  "reference to a local variable or value.",
        #                  line=ret_line)
        # if not self.ret_type.returnable and self.block is None:
        #     errors.warning("THIS IS NOT AN ERROR\n" +
        #                    "You are binding a function that returns a heap pointer.\n" +
        #                    "You will not be able to free this memory!\n" +
        #                    "Please keep this in mind",
        #                    line=ret_line)
        if self.visibility == Modifiers.VISIBILITY_PUBLIC and self.ret_type.visibility == Modifiers.VISIBILITY_PRIVATE:
            errors.error("Function is public while the return type is private. \n" +
                         "This makes it impossible for external callers to handle the return.",
                         line=ret_line)

    def _mangle_name(self, name, parent: Parent) -> str:
        '''add an ID to the end of a name if the function has a body and
        is NOT named "main"'''
        if parent == self.module and self.block is None:
            if name in self.module.globals.keys():
                errors.error(f"Bound function with the name \"{name}\" already exists",
                             line=self.position, full_line=True)
            return name
        return parent.get_unique_name(name)

    def _append_args(self):
        '''append all args as variables usable inside the function body'''
        args = self.function_ir.args
        for c, x in enumerate(self.args.keys()):
            orig = self.args[x]
            # print(orig[1])
            var = VariableObj(orig[0], orig[1], True, orig[3])
            self.block.variables[x] = var
            self.block.variables[x].ptr = args[c]
            self.variables.append((self.block.variables[x], x))

    def validate_variable_exists(self, var_name, module=None):
        if var_name in self.args.keys():
            return self.get_variable(var_name, module)
        elif self.parent is not None:
            return self.parent.validate_variable_exists(var_name, module)
        elif module is not None:
            return module.get_global(var_name)

    def get_variable(self, var_name, module=None):
        ''' when the block is a child of this node,
        this function is used to find arguments as variables
        '''
        if var_name in self.args.keys():
            orig = self.args[var_name]
            var = VariableObj(orig[0], orig[1], True, orig[3])
            return var
        elif self.parent is not None:
            return self.parent.get_variable(var_name, module)
        elif module is not None:
            return module.get_global(var_name)

    def fullfill_templates(self, func):
        if self.block is not None:
            self.block.parent = self
            self.block.fullfill_templates(func)
        self.raw_args.fullfill_templates(func)
        if not isinstance(self.ret_raw, Type):
            self.ret_raw.fullfill_templates(func)

    def post_parse(self, parent: Parent):
        if self.block is not None:
            self.block.parent = self
        self._validate_return(self)
        self._construct_args(self.raw_args, parent)

        if self.block is not None:
            self.block.post_parse(self)

        if self.yields and self.ret_type.is_void():
            errors.error("Generator Functions have a return a value",
                         line=self.position)

        if self.yields:
            fnty = ir.FunctionType(ir.VoidType(),
                                   (self.ret_type.ir_type.as_pointer(),))

            self.yield_function = ir.Function(self.module.module, fnty,
                                              name=self._mangle_name(self.func_name+".gen",
                                                                     parent))
            self.yield_block = self.yield_function.append_basic_block("entry")
            self.yield_start = self.yield_function.append_basic_block("start")

        fnty = ir.FunctionType((self.ret_type).ir_type, self.args_ir,
                               self.contains_ellipsis)

        self.function_ir = ir.Function(self.module.module, fnty,
                                       name=self._mangle_name(self.func_name,
                                                              parent))
        function_object = Ast_Types.Function(self.func_name, self.args_types,
                                             self.function_ir, self.module,
                                             self)
        if self.block is None and platform.system() == "windows":
            self.function_ir.linkage += "dllimport"
        function_object.add_return(self.ret_type) \
                       .set_ellipses(self.contains_ellipsis) \
                       .set_method(self.is_method, parent) \
                       .set_visibility(self.visibility)

        self.function_ty = function_object

        parent.create_function(self.func_name, function_object)

    def pre_eval(self, parent: Parent):
        # Early return if the function has no body.
        if self.has_no_body:
            return

        block = self.function_ir.append_basic_block("entry")
        self.builder = ir.IRBuilder(block)
        self.ir_entry = block
        self._append_args()
        self.block.pre_eval(self)

    def create_const_var(self, typ):
        current_block = self.builder.block
        self.builder.position_at_start(self.ir_entry)
        if self.yields:
            self.yield_consts.append(typ)
            self.yield_gen_type.add_members(self.yield_consts, [x[0].type for x in self.variables])
            ptr = self.builder.gep(self.yield_struct_ptr,
                                   [ir.Constant(ir.IntType(32), 0),
                                    ir.Constant(ir.IntType(32), 3),
                                    ir.Constant(ir.IntType(32),
                                                len(self.yield_consts)-1)],
                                   name="CONST")
            self.builder.position_at_end(current_block)

            return ptr
        ptr = self.builder.alloca(typ.ir_type, name="CONST")
        self.builder.position_at_end(current_block)
        return ptr

    def alloc_stack_gen_create(self):
        for c, x in enumerate(self.variables):
            if x[0].is_constant:
                if x[0].type.pass_as_ptr:
                    val = self.builder.load(x[0].ptr)
                else:
                    val = x[0].ptr
                if not x[0].type.no_load:
                    ptr = self.builder.gep(self.yield_struct_ptr,
                                           [ir.Constant(ir.IntType(32), 0),
                                            ir.Constant(ir.IntType(32), 4),
                                            ir.Constant(ir.IntType(32), c)])
                    self.builder.store(val, ptr)
                    x[0].ptr = ptr
                continue

    def alloc_stack_gen(self):
        for c, x in enumerate(self.variables):
            if x[0].is_constant:
                if not x[0].type.no_load:
                    ptr = self.builder.gep(self.yield_struct_ptr,
                                           [ir.Constant(ir.IntType(32), 0),
                                            ir.Constant(ir.IntType(32), 4),
                                            ir.Constant(ir.IntType(32), c)])
                    x[0].ptr = ptr
                x[0].is_constant = False
                continue
            else:
                x[0].define(self, x[1], c)

    def alloc_stack(self):
        # TODO: REFACTOR
        for c, x in enumerate(self.variables):
            if x[0].is_constant:
                # if x[0].type.pass_as_ptr:
                #     val = self.builder.load(x[0].ptr)
                # else:
                #     val = x[0].ptr
                # if not x[0].type.no_load:
                #     ptr = self.builder.alloca(x[0].type.ir_type)
                #     self.builder.store(val, ptr)
                #     x[0].ptr = ptr
                x[0].type.recieve(self, x)
                x[0].is_constant = False
            else:
                x[0].define(self, x[1], c)

    def eval_impl(self, parent):
        if self.has_no_body:
            return
        self.function_ir.attributes.add("nounwind")

        if not self.yields:
            self.alloc_stack()
            self.block.eval(self)
        else:
            self.yield_struct_ptr = self.builder.alloca(self.ret_type.ir_type)
            self.yield_gen_type = self.ret_type
            self.yield_gen_type.add_members(self.yield_consts, [x[0].type for x in self.variables])
            self.populate_yield_struct()
            self.alloc_stack_gen_create()
            self.yield_gen_type.create_next_method()
            val = self.builder.load(self.yield_struct_ptr)
            self.builder.ret(val)
            self.eval_generator(parent)

        if self.ret_type.is_void() and not self.has_return:
            self.dispose_stack()
            self.builder.ret_void()
        elif not self.has_return:
            errors.error(f"Function '{self.func_name}' has no guaranteed " +
                         "return!\nEnsure that at least 1 return statement is" +
                         " reachable!\n hint: return should happend " +
                         "regardless of branching!",
                         line=self._position, full_line=True)

    def eval_generator(self, parent):
        self.ret_type = Ast_Types.Void()

        self.function_ir = self.yield_function

        if self.has_no_body:
            return

        block = self.yield_block
        self.builder = ir.IRBuilder(self.yield_block)
        self.yield_struct_ptr = self.yield_function.args[0]

        self.alloc_stack_gen()
        self.ir_entry = block
        state_ptr = self.builder.gep(self.yield_struct_ptr,
                                     [ir.Constant(ir.IntType(32), 0),
                                      ir.Constant(ir.IntType(32), 1)])
        self.builder.position_at_start(self.yield_start)
        self.block.eval(self)
        after_block = self.builder.block

        self.builder.position_at_end(block)

        # Do branching on function entry
        state = self.builder.load(state_ptr)
        ibranch = self.builder.branch_indirect(state)
        ibranch.add_destination(self.yield_start)
        for branch in self.yield_after_blocks:
            ibranch.add_destination(branch)

        self.builder.position_at_end(after_block)
        if not self.builder.block.is_terminated:
            continue_ptr = self.builder.gep(self.yield_struct_ptr,
                                            [ir.Constant(ir.IntType(32), 0),
                                                ir.Constant(ir.IntType(32), 0)])
            self.builder.store(ir.Constant(ir.IntType(1), 0), continue_ptr)

        self.yield_gen_type.add_members(self.yield_consts, [x[0].type for x in self.variables])

    def populate_yield_struct(self):
        continue_ptr = self.builder.gep(self.yield_struct_ptr,
                                        [ir.Constant(ir.IntType(32), 0),
                                         ir.Constant(ir.IntType(32), 0)])
        state_ptr = self.builder.gep(self.yield_struct_ptr,
                                     [ir.Constant(ir.IntType(32), 0),
                                      ir.Constant(ir.IntType(32), 1)])
        self.builder.store(ir.Constant(ir.IntType(1), 1), continue_ptr)
        block_addr = ir.BlockAddress(self.yield_function, self.yield_start)
        self.builder.store(block_addr, state_ptr)

    def dispose_stack(self):
        self.block.BLOCK_STACK.append(self.block)

        for node in self.dispose_queue:
            node.ret_type.dispose(self, node)

        self.block.BLOCK_STACK.pop()

    @property
    def has_no_body(self) -> bool:
        return self.block is None

    def repr_as_tree(self) -> str:
        return self.create_tree("Function Definition",
                                name=self.func_name,
                                contents=self.block,
                                return_type=self.ret_type)
