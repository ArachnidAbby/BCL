import platform
from typing import TYPE_CHECKING, NoReturn, Optional, Self

from llvmlite import ir

import errors
from Ast.Ast_Types.Type_Base import Type
from Ast.Ast_Types.Type_Reference import Reference
from Ast.Ast_Types.Type_Void import Void  # type: ignore
from Ast.math import MemberAccess
from Ast.nodes.commontypes import Modifiers, SrcPosition
from Ast.nodes.expression import ExpressionNode
from Ast.nodes.passthrough import PassNode
from Ast.reference import Ref
from errors import error

if TYPE_CHECKING:
    from Ast.functions.call import FunctionCall
    from Ast.module import NamespaceInfo


class MockFunction:
    __slots__ = ("builder", "module")

    def __init__(self, builder, module):
        self.builder = builder
        self.module = module


class NodeLifetimePass(ExpressionNode):
    __slots__ = ('lifetime', 'node', 'mapped_from', 'args_list')

    def __init__(self, pos, lifetime, node, mapped, args):
        self._position = pos
        self.lifetime = lifetime
        self.node = node
        self.mapped_from: tuple[ExpressionNode, int] = mapped
        self.args_list = args

    def get_lifetime(self, func):
        return self.lifetime

    def get_recursion_depth(self, recursion_depth=0):
        if not isinstance(self.mapped_from[0], NodeLifetimePass):
            return recursion_depth

        return self.mapped_from[0].get_recursion_depth(recursion_depth) + 1

    def get_mapped_arg_pos(self, recursion_amount=0, max_recursion=0):
        if not isinstance(self.mapped_from[0], NodeLifetimePass) or \
                recursion_amount >= max_recursion:
            return self.mapped_from[1]

        return self.mapped_from[0].get_mapped_arg_pos(recursion_amount+1,
                                                      max_recursion=max_recursion)

    def get_arg_list(self, recursion_amount=0, max_recursion=0):
        if not isinstance(self.mapped_from[0], NodeLifetimePass) or \
                recursion_amount >= max_recursion:
            return self.args_list

        return self.mapped_from[0].get_arg_list(recursion_amount+1,
                                                max_recursion=max_recursion)

    # def __str__(self) -> str:
    #     return f"[LIFETIME:{self.lifetime}, node: {str(self.node)}]"

    def get_position(self) -> SrcPosition:
        if not isinstance(self.node, NodeLifetimePass):
            return self.node.get_position()
        return super().get_position()

    def __str__(self) -> str:
        return str(self.node)

    def __getattr__(self, name):
        return getattr(self.node, name)


class Function(Type):
    '''abstract type class that outlines the necessary features
    of a type class.'''

    __slots__ = ('func_name', 'module', 'args', 'func_ret',
                 'contains_ellipsis', "func_obj", "is_method",
                 "visibility", "lifetime_groups", "definition",
                 "call_stack", "coupled_functions", "return_coupling")

    name = "Function"
    pass_as_ptr = False
    no_load = False
    read_only = True

    def __init__(self, name: str, args: tuple, func_obj, module,
                 definition):
        self.func_name = name
        self.module = module
        self.args = args
        self.func_ret: Type = Void()
        # Contains the actually llvm function
        self.func_obj = func_obj
        self.contains_ellipsis = False
        self.is_method = False
        self.lifetime_groups = []

        # all of these must have *equal* return. tight coupling
        self.return_coupling = []
        # functions that get called inside of this one.
        # These have their own lifetime checks
        coupled_args = tuple[tuple[int, int], ...]
        self.coupled_functions: list[tuple[Function, coupled_args,
                                           FunctionCall]] = []

        # used when resolving coupling and lifetime dependence.
        self.call_stack = []
        self.visibility = super().visibility
        self.definition = definition

    def couple_lifetimes(self, arg1_id, arg2_id):
        coupling = (arg1_id, arg2_id)
        if coupling not in self.lifetime_groups:
            self.lifetime_groups.append(coupling)

    def lifetime_checks(self, func, args):
        for group in self.lifetime_groups:
            arg0_lifetime = args[group[0]].get_lifetime(func)
            arg1_lifetime = args[group[1]].get_lifetime(func)
            if arg0_lifetime.value > arg1_lifetime.value:
                if not isinstance(args[group[0]], NodeLifetimePass):
                    self._lifetime_error_regular(group, args)
                else:
                    self._lifetime_error_mapped(group, args)

    def _lifetime_error_regular(self, group, args):
        error(f"Arguments {group[0]} and {group[1]} have a coupled " +
              f"lifetime. \nThe argument: \"{args[group[0]]}\"\n" +
              "must have a lifetime less than or\n" +
              f"equal to argument: \"{args[group[1]]}\"",
              line=[args[group[0]].position, args[group[1]].position])

    def _lifetime_return_error_regular(self, group, args):
        error(f"Arguments {group[0]} and {group[1]} have a STRONGLY" +
              " coupled\nlifetime due to both being returned by the" +
              f" callee.\nThe argument: \"{args[group[0]]}\"\n" +
              "must have a lifetime " +
              f"equal to\nthe argument: \"{args[group[1]]}\"",
              line=[args[group[0]].position, args[group[1]].position])

    def _lifetime_error_mapped(self, group, args):
        min_depth = min(
            args[group[0]].get_recursion_depth(),
            args[group[1]].get_recursion_depth()
        )

        new_args = args[group[0]].get_arg_list(max_recursion=min_depth)
        group = (
            args[group[0]].get_mapped_arg_pos(max_recursion=min_depth),
            args[group[1]].get_mapped_arg_pos(max_recursion=min_depth)
        )
        args = new_args
        error(f"Arguments {group[0]} and {group[1]} have a coupled " +
              f"lifetime. \nThe argument: \"{args[group[0]]}\"\n" +
              "must have a lifetime less than or\n" +
              f"equal to argument: \"{args[group[1]]}\"",
              line=[args[group[0]].position, args[group[1]].position])

    def _lifetime_return_error_mapped(self, group, args):
        min_depth = min(
            args[group[0]].get_recursion_depth(),
            args[group[1]].get_recursion_depth()
        )

        new_args = args[group[0]].get_arg_list(max_recursion=min_depth)
        group = (
            args[group[0]].get_mapped_arg_pos(max_recursion=min_depth),
            args[group[1]].get_mapped_arg_pos(max_recursion=min_depth)
        )
        args = new_args
        error(f"Arguments {group[0]} and {group[1]} have a STRONGLY " +
              "coupled\n lifetime due to both being returned by the" +
              f" callee.\nThe argument: \"{args[group[0]]}\"\n" +
              "must have a lifetime " +
              f"equal to\nthe argument: \"{args[group[1]]}\"",
              line=[args[group[0]].position, args[group[1]].position])

    def check_return_coupling(self, func, args):
        needed_lifetime = None
        needed_life_item = 0
        for item in self.return_coupling:
            item_val = args[item]
            item_life = item_val.get_lifetime(func)

            if needed_lifetime is None:
                needed_lifetime = item_life
                needed_life_item = item
                continue

            if needed_lifetime.value != item_life.value:
                if not isinstance(item_val, NodeLifetimePass):
                    self._lifetime_return_error_regular((needed_life_item,
                                                         item),
                                                        args)
                else:
                    self._lifetime_return_error_mapped((needed_life_item,
                                                        item),
                                                       args)

    def check_function_coupling(self, func, args, recursion_amount=0):
        if self in self.call_stack:
            return
        self.call_stack.append(self)

        for coupled in self.coupled_functions:
            coupled_func = coupled[0]

            orig_args = coupled[2].paren.children
            coupled[2].paren.children = \
                coupled_func._fix_args(coupled[2].func_name,
                                       coupled[2].paren,
                                       self.definition)
            new_args = [_ for _ in coupled[2].paren.children]
            coupled[2].paren.children = orig_args
            # new_args = [coupled[2].func_name.lhs] + new_args

            for o_idx, coupled_args_lhs in coupled[1]:
                arg = args[coupled_args_lhs]
                new_args[o_idx] = NodeLifetimePass(arg.position,
                                                   arg.get_lifetime(func),
                                                   new_args[o_idx],
                                                   (arg, coupled_args_lhs),
                                                   args)
            coupled_func.check_return_coupling(self.definition, new_args)
            coupled_func.lifetime_checks(self.definition, new_args)
            coupled_func.check_function_coupling(self.definition, new_args)

        self.call_stack.pop(-1)

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
        # ! any way to avoid try catch?
        try:
            fnty = ir.FunctionType((self.func_ret).ir_type,
                                   self.get_ir_types(),
                                   self.contains_ellipsis)
            functy = ir.Function(module.module, fnty,
                                 name=self.func_obj.name)
            if self.definition is not None:
                functy.linkage = self.func_obj.linkage
        except ir._utils.DuplicatedNameError:
            error("Bound function with the name " +
                  f"\"{self.func_obj.name}\" already exists",
                  line=self.definition.position, full_line=True)

        if self.func_ret.name != "Generator":
            return

        self.func_ret.declare(module)

    @classmethod
    def convert_from(cls, func, typ, previous) -> None:
        error("Function type has no conversions",  line=previous.position)

    def convert_to(self, func, orig, typ) -> None:
        error("Function type has no conversions",  line=orig.position)

    def __eq__(self, other):
        return super().__eq__(other) and \
            other.func_name == self.func_name and \
            self.module == other.module

    def __neq__(self, other):
        return super().__neq__(other) or \
            other.func_name != self.func_name or \
            self.module != other.module

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
            if isinstance(lhs, MemberAccess) and self.is_method and c == 0:
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
        self.check_return_coupling(func, args.children)
        self.lifetime_checks(func, args.children)
        self.check_function_coupling(func, args.children)
        args.children = orig_args
        return func.builder.call(self.func_obj, args.evaled_children)

    def __hash__(self):
        return hash(self.name + self.func_name)

    def __repr__(self) -> str:
        return f'<Type: {self.name}--{self.func_name}>'

    def __str__(self) -> str:
        return f"{self.func_name}{str(self.args)} -> {self.func_ret}"

    def get_signature(self) -> str:
        str_ret = str(self.definition.ret_type)
        str_args = ', '.join([str(arg) for arg in self.args])
        return f"({str_args}) -> {str_ret}"

    def __call__(self) -> Self:
        return self


class FunctionGroup(Type):
    '''Function Group
    Functions of the same name are said to belong to the same group.
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

    def get_function(self, func, lhs, args) -> Function | NoReturn:
        private_matches = 0
        for version in self.versions:
            if version.match_args(lhs, args):
                if version.visibility != Modifiers.VISIBILITY_PUBLIC and \
                        version.module.location != func.module.location:
                    private_matches += 1
                    continue
                return version
        self.print_call_error(lhs, args, private_matches)

    def print_call_error(self, lhs, rhs, private_matches) -> NoReturn:
        if private_matches > 0:
            error("A valid version of this function does exist for these " +
                  "arguments, but it is private", line=lhs.position)

        if len(self.versions) == 0:
            note_message = "note: the function could also not exist."
        else:
            # very confusing tbh
            start = f"{errors.RED}|   {errors.RESET}"
            signatures = [f"{start}{ver.get_signature()}"
                          for ver in self.versions]
            note_message = "This function takes any of these arguments:\n" + \
                           ",\n".join(signatures)

        str_args = ', '.join([str(x.ret_type) for x in rhs])
        error("Invalid Argument types for function group with \n" +
              f" name: {self.func_name}\n args: ({str_args})",
              note=note_message,
              line=rhs.position)

    def call(self, func, lhs, args: tuple):
        return self.get_function(func, lhs, args).call(func, lhs, args)

    def assign(self, func, ptr, value, typ: Self, first_assignment=False):
        error("Variables cannot be set to a FunctionGroup",
              line=value.position)

    # required to fullfill "Namespace" protocol
    def get_global(self, name: str,
                   pos=SrcPosition.invalid(), stack=None,
                   override_star=False) -> Optional["NamespaceInfo"]:
        pass


class FakeOpFunction(Function):
    __slots__ = ('callback', 'arg_count', 'op_name', 'typ')

    def __init__(self, name, op_name, typ, callback,
                 arg_count):
        super().__init__(name, (), None, None, None)
        self.callback = callback
        self.is_method = True
        self.arg_count = arg_count
        self.op_name = op_name
        self.typ = typ

    def __eq__(self, other):
        return super().__eq__(other) and \
            other.callback == self.callback

    def __neq__(self, other):
        return super().__neq__(other) or \
            other.callback != self.callback

    def deref(self, func, lhs, rhs) -> tuple:
        if self.typ.name == "STRUCT":
            return lhs, rhs

        if rhs is None:
            return lhs, rhs

        if isinstance(rhs.ret_type, Reference):

            ptr = rhs.eval(func)

            rhs = PassNode(rhs.position,
                           func.builder.load(ptr),
                           rhs.ret_type.typ,
                           ptr)
        return lhs, rhs

    def get_op_return(self, func, op, lhs, rhs):
        from Ast.Ast_Types.Type_Bool import Integer_1
        from Ast.math import check_valid_inplace

        if op != "call":
            return

        args = rhs.children
        if isinstance(lhs, MemberAccess):
            lhs.lhs.pre_eval(func)
            args = [lhs.lhs] + args
        if len(args) != self.arg_count:
            error("Invalid number of arguments on operation function" +
                  f" for type {self.typ}", line=rhs.position)

        # check for inplace ops
        # ! This is kinda dumb
        if self.func_name.startswith("__i"):
            check_valid_inplace(args[0])
        if self.func_name != "__call__":
            rhs_ = None if len(args) == 1 else args[1]
            args = list(self.deref(func, args[0], rhs_))
        # if args[1] is None:
        #     args.pop(1)

        if self.op_name == "__deref__":
            return self.typ.get_deref_return(func, *args)
        elif self.op_name == "__truthy__":
            return Integer_1()
        elif self.op_name == "call":
            ret_type = self.typ.get_op_return(func, self.op_name,
                                              args[0], rhs)
        else:
            ret_type = self.typ.get_op_return(func, self.op_name, *args)

        if ret_type is None:
            error(f"Type \"{self.typ}\" does not have method \"{self.func_name}\"",
                  line=lhs.position)
        return ret_type

    def call(self, func, lhs, args):
        from Ast.math import check_valid_inplace

        args_ = args.children
        if isinstance(lhs, MemberAccess):
            args_ = [lhs.lhs] + args_

        if self.func_name != "__call__":
            rhs_ = None if len(args_) == 1 else args_[1]
            args_ = list(self.deref(func, args_[0], rhs_))
            if args_[1] is None:
                args_.pop(1)

        # check for inplace ops
        # ! This is kinda dumb
        if self.func_name.startswith("__i"):
            check_valid_inplace(args_[0])

        elif self.op_name == "call":
            return self.callback(func, args_[0], args)
        return self.callback(func, *args_)
