from llvmlite import ir
from Ast.Ast_Types.Type_Function import Function, FunctionGroup
from Ast.Ast_Types.Type_Reference import Reference
from Ast.Ast_Types.Type_Void import Void
from Ast.nodes.commontypes import MemberInfo

import errors
from Ast.Ast_Types.Type_Base import Type


class UntypedPointer(Type):
    name = 'UntypedPointer'
    ir_type: ir.Type = ir.IntType(8).as_pointer()

    no_load = True
    has_members = True
    read_only = False
    returnable = True
    needs_dispose = True
    ref_counted = True
    generate_bounds_check = False

    def convert_to(self, func, orig, typ):
        if self.roughly_equals(typ):
            return func.builder.bitcast(orig.eval(func), typ.ir_type)

        errors.error("Cannot convert UntypedPointer to non-pointer type",
                     line=orig.position)

    def get_op_return(self, func, op, lhs, rhs):
        self._simple_call_op_error_check(op, lhs, rhs)
        if op == "ind":
            return self

    def get_member_info(self, lhs, rhs):
        if rhs.var_name not in ("store", "release", "retake"):
            return None
            errors.error("member not found!", line=rhs.position)
        typ = None
        if rhs.var_name == "store":
            typ = store_func
        elif rhs.var_name == "release":
            typ = release_func
        elif rhs.var_name == "retake":
            typ = retake_func
        return MemberInfo(not typ.read_only, False, typ)

    def get_member(self, func, lhs,
                   member_name_in: "Ast.variable.VariableRef"):
        member_name = member_name_in.var_name
        if member_name == "store":
            return store_func
        elif member_name == "release":
            return release_func
        elif member_name == "retake":
            return retake_func

    def roughly_equals(self, other):
        return isinstance(other, Reference) or self == other

    def index(self, func, lhs, rhs):
        # val = Integer_32(64, 'u64', signed=False)
        return func.builder.gep(lhs.eval(func),
                                [rhs.eval(func), ])

    def pass_to(self, func, item):
        if item.ret_type == self:
            return item.eval(func)

        return func.builder.bitcast(item.eval(func), self.ir_type)


class StoreFunction(Function):
    '''Overload default Function Type behavior'''

    __slots__ = ()

    def __init__(self):
        super().__init__("store", (), None, None)
        self.func_ret = Void()
        self.is_method = True
        self.args = (UntypedPointer(), )

    def match_args(self, lhs, args):
        from Ast.Ast_Types.Type_Reference import Reference
        args_used = args.children
        if len(args_used) != 1:
            return False

        if not isinstance(args_used[0].ret_type, Reference):
            return False

        # if not isinstance(args_used[1].ret_type, definedtypes.types_dict["size_t"]):
        #     return False

        return True

    def call(self, func, lhs, rhs):
        args_used = rhs.children
        lhs = lhs.lhs
        data = args_used[0].eval(func)
        actual_ptr = func.builder.bitcast(lhs.eval(func), args_used[0].ret_type.ir_type)
        # print(actual_ptr)
        # print(args_used[0].ret_type.ir_type)
        # print(args_used)
        # print(data)
        # print()
        # old_name = func.func_name
        # func.func_name = "store"
        # args_used[0].ret_type.add_ref_count(func, args_used[0])
        # func.func_name = old_name
        ptr_val = func.builder.load(data)
        func.builder.store(ptr_val, actual_ptr)


class RetakeFunction(StoreFunction):
    def call(self, func, lhs, rhs):
        args_used = rhs.children
        old_name = func.func_name
        func.func_name = "retake"
        args_used[0].ret_type._add_ref_count(func, args_used[0])
        func.func_name = old_name


class ReleaseFunction(StoreFunction):
    def call(self, func, lhs, rhs):
        args_used = rhs.children
        old_name = func.func_name
        func.func_name = "release"
        args_used[0].ret_type._dispose(func, args_used[0])
        func.func_name = old_name


store_func = FunctionGroup("store", None)
store_func.add_function(StoreFunction())

release_func = FunctionGroup("release", None)
release_func.add_function(ReleaseFunction())

retake_func = FunctionGroup("retake", None)
retake_func.add_function(RetakeFunction())
