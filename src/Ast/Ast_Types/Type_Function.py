from typing import Self

from llvmlite import ir
from Ast.Ast_Types.Type_Base import Type
from Ast.Ast_Types.Type_Reference import Reference
from Ast.Ast_Types.Type_Void import Void# type: ignore

# from Ast import Ast_Types
# from Ast.Ast_Types import Type_Base
from Ast.math import MemberAccess
from Ast.reference import Ref
from errors import error
from Ast.nodes.commontypes import Modifiers


class MockFunction:
    __slots__ = ("builder", "module")

    def __init__(self, builder, module):
        self.builder = builder
        self.module = module


class Function(Type):
    '''abstract type class that outlines the necessary features
    of a type class.'''

    __slots__ = ('func_name', 'module', 'args', 'func_ret',
                 'contains_ellipsis', "func_obj", "is_method",
                 "visibility", "lifetime_groups")

    name = "Function"
    pass_as_ptr = False
    no_load = False
    read_only = True

    def __init__(self, name: str, args: tuple, func_obj, module):
        self.func_name = name
        self.module = module
        self.args = args
        self.func_ret: Type = Void()
        # Contains the actually llvm function
        self.func_obj = func_obj
        self.contains_ellipsis = False
        self.is_method = False
        self.lifetime_groups = []
        self.visibility = super().visibility

    def couple_lifetimes(self, arg1_id, arg2_id):
        coupling = (arg1_id, arg2_id)
        if coupling not in self.lifetime_groups:
            self.lifetime_groups.append(coupling)

    def lifetime_checks(self, func, args):
        # print("POGGERS")
        for group in self.lifetime_groups:
            arg0_lifetime = args[group[0]].get_lifetime(func)
            arg1_lifetime = args[group[1]].get_lifetime(func)
            if arg0_lifetime.value > arg1_lifetime.value:
                pos = args[group[0]].merge_pos([args[group[1]].position])
                error(f"Arguments {group[0]} and {group[1]} have a coupled " +
                      f"lifetime. \nThe argument: \"{args[group[0]]}\"\n" +
                      "must have a lifetime less than or\n" +
                      f"equal to argument: \"{args[group[1]]}\"", line=pos)

    def add_return(self, ret: Type):
        self.func_ret = ret
        return self

    def set_ellipses(self, ellipsis):
        self.contains_ellipsis = ellipsis
        return self

    def set_method(self, method, parent):
        self.is_method = method
        return self

    def set_visibility(self, value):
        self.visibility = value
        return self

    def get_ir_types(self):
        ir_types = []
        for arg in self.args:
            if arg.pass_as_ptr:
                ir_types.append(arg.ir_type.as_pointer())
            else:
                ir_types.append(arg.ir_type)
        return tuple(ir_types)

    def declare(self, module):
        '''Declare a function inside of a new module'''
        fnty = ir.FunctionType((self.func_ret).ir_type, self.get_ir_types(),
                               self.contains_ellipsis)
        ir.Function(module.module, fnty,
                    name=module.get_unique_name(self.func_obj.name))

        if self.func_ret.name != "Generator":
            return

        self.func_ret.declare(module)

    @classmethod
    def convert_from(cls, func, typ, previous) -> ir.Instruction:
        error("Function type has no conversions",  line=previous.position)

    def convert_to(self, func, orig, typ) -> ir.Instruction:
        error("Function type has no conversions",  line=orig.position)

    def __eq__(self, other):
        return super().__eq__(other) and \
            other.func_name == self.func_name

    def __neq__(self, other):
        return super().__neq__(other) and \
            other.func_name != self.func_name

    def get_op_return(self, func, op, lhs, rhs):
        if op != "call":
            return
        # rhs is the argument tuple
        if self.match_args(lhs, rhs):
            return self.func_ret
        else:
            self.print_call_error(rhs)

    def print_call_error(self, rhs):
        error("Invalid Argument types for function" +
              f"{str(self)}",
              line=rhs.position)

    def _fix_args(self, lhs, args, func=None):
        if isinstance(lhs, MemberAccess) and self.is_method:
            if func is not None:
                if isinstance(self.args[0], Reference):
                    ref = Ref(lhs.lhs.position, lhs.lhs)
                    ref.pre_eval(func)
                    return [ref, *args.children]
            return [lhs.lhs, *args.children]
        else:
            return args.children

    def match_args(self, lhs, args):
        args_used = self._fix_args(lhs, args)

        if not self.contains_ellipsis and len(args_used) != len(self.args):
            return False
        if self.contains_ellipsis and len(args_used) < len(self.args):
            return False

        for c, (func_arg, passed_arg) in enumerate(zip(self.args, args_used)):
            if isinstance(lhs, MemberAccess) and self.is_method and c==0:
                continue
            if not func_arg.roughly_equals(passed_arg.ret_type):
                return False

        return True

    def call(self, func, lhs, args):
        # * prevent adding additional args multiple times
        # * when doing .eval(func) multiple times
        orig_args = args.children
        if len(args.children) != len(self.args):
            args.children = self._fix_args(lhs, args, func)
        args.eval(func, expected_args=self.args)
        self.lifetime_checks(func, args.children)
        args.children = orig_args
        return func.builder.call(self.func_obj, args.evaled_children)

    def __hash__(self):
        return hash(self.name+self.struct_name)

    def __repr__(self) -> str:
        return f'<Type: {self.name}--{self.func_name}>'

    def __str__(self) -> str:
        return f"{self.func_name}{str(self.args)}->{self.func_ret}"

    def __call__(self) -> Self:
        return self


class FunctionGroup(Type):
    '''Function Group
    Functions of the same name are said to belong to the same group.
    *test*
    '''
    __slots__ = ('func_name', 'module', 'versions')
    name = "FunctionGroup"
    pass_as_ptr = False
    no_load = False
    read_only = True

    def __init__(self, name: str, module):
        self.func_name = name
        self.module = module
        self.versions: list[Function] = []

    def add_function(self, func: Function):
        self.versions.append(func)
        return self

    def declare(self, module):
        '''Declare a function inside of a new module'''
        for func in self.versions:
            func.declare(module)

    def get_op_return(self, func, op, lhs, rhs):
        if op != "call":
            return
        # rhs is the argument tuple
        return self.get_function(func, lhs, rhs).func_ret

    def get_function(self, func, lhs, args):
        private_matches = 0
        for version in self.versions:
            if version.match_args(lhs, args):
                if version.visibility != Modifiers.VISIBILITY_PUBLIC and \
                        version.module.location != func.module.location:
                    private_matches += 1
                    continue
                return version
        self.print_call_error(lhs, args, private_matches)

    def print_call_error(self, lhs, rhs, private_matches):
        if private_matches > 0:
            error("A valid version of this function does exist for these " +
                  "arguments, but it is private", line=lhs.position)

        error("Invalid Argument types for function group with \n" +
              f" name: {self.func_name}\n args: ({', '.join([str(x.ret_type) for x in rhs])})",
              line=rhs.position)

    def call(self, func, lhs, args: tuple):
        return self.get_function(func, lhs, args).call(func, lhs, args)

    def assign(self, func, ptr, value, typ: Self, first_assignment=False):
        error("Variables cannot be set to a FunctionGroup", line=value.position)
