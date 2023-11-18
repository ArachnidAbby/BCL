from llvmlite import ir

import Ast.exception
from Ast.Ast_Types.Type_Base import Type
from Ast.Ast_Types.Type_Function import Function, FunctionGroup, MockFunction
from Ast.Ast_Types.Type_Reference import Reference
from Ast.nodes.commontypes import MemberInfo, SrcPosition
from errors import error


def create_next_method(module, gen_typ, name):
    function_ty = ir.FunctionType(gen_typ.typ.ir_type,
                                  (gen_typ.ir_type.as_pointer(), ))
    func = ir.Function(module.module, function_ty, f"{name}.next")
    block = func.append_basic_block(name="entry")
    builder = ir.IRBuilder(block)
    arg = func.args[0]
    mock_func = MockFunction(builder, module)

    orig_block_name = builder.block._name
    body_name = f'{orig_block_name}.if'
    end_name = f'{orig_block_name}.endif'
    check_body = builder.append_basic_block(body_name)
    check_after = builder.append_basic_block(end_name)

    value = gen_typ.iter(mock_func, arg, SrcPosition.invalid())
    cond = gen_typ.iter_condition(mock_func, arg, SrcPosition.invalid())
    builder.cbranch(cond, check_after, check_body)

    builder.position_at_start(check_body)
    Ast.exception.no_next_item(mock_func, module.mod_name)
    builder.unreachable()

    builder.position_at_start(check_after)
    builder.ret(value)
    return func


class GeneratorType(Type):
    __slots__ = ("iter_function", "ir_type", "typ", "next", "next_group")

    is_iterator = True
    has_members = True
    name = "Generator"

    def __init__(self, iter_function, typ):
        self.iter_function = iter_function
        self.typ = typ
        # {continue: i1, state: i8*, result: typ, ...}
        self.ir_type = ir.global_context.get_identified_type(f"struct.{iter_function.func_name}")
        self.next_group = FunctionGroup("next", self.iter_function.module)
        mod = self.iter_function.module
        self.next = Function("next", (Reference(self),), None, mod, None)
        self.next.set_method(True, self)
        self.next.add_return(self.typ)
        self.next_group.add_function(self.next)

    def create_next_method(self):
        mod = self.iter_function.module
        func_obj = create_next_method(mod, self, self.iter_function.func_name)
        self.next.func_obj = func_obj

    def declare(self, module):
        self.next.declare(module)

        fnty = ir.FunctionType(ir.VoidType(),
                               (self.ir_type.as_pointer(),))

        ir.Function(module.module, fnty,
                    name=self.iter_function.yield_function.name)

    def add_members(self, consts, members):
        # Doing the dangerous thing and setting the elements directly
        # Not doing this causes an error... probably for good reason...
        # but I can't do it any other way.
        self.ir_type.elements = (
            ir.IntType(1),
            ir.IntType(8).as_pointer(),
            self.typ.ir_type,
            ir.LiteralStructType([x.ir_type for x in consts]),
            ir.LiteralStructType([x.ir_type for x in members])
        )

    def set_value(self, func, value, block):
        continue_ptr = func.builder.gep(func.yield_struct_ptr,
                                        [ir.Constant(ir.IntType(32), 0),
                                         ir.Constant(ir.IntType(32), 0)])
        value_ptr = func.builder.gep(func.yield_struct_ptr,
                                     [ir.Constant(ir.IntType(32), 0),
                                      ir.Constant(ir.IntType(32), 2)])
        state_ptr = func.builder.gep(func.yield_struct_ptr,
                                     [ir.Constant(ir.IntType(32), 0),
                                      ir.Constant(ir.IntType(32), 1)])
        func.builder.store(value, value_ptr)
        func.builder.store(ir.Constant(ir.IntType(1), 1), continue_ptr)
        block_addr = ir.BlockAddress(func.yield_function, block)
        func.builder.store(block_addr, state_ptr)

    def get_member_info(self, lhs, rhs):
        if rhs.var_name != "next":
            return None
            error("member not found!", line=rhs.position)
        typ = self.next
        return MemberInfo(not typ.read_only, False, typ)

    def get_member(self, func, lhs,
                   member_name_in: "Ast.variable.VariableRef"):
        member_name = member_name_in.var_name
        if member_name == "next":
            return self.next

    def __eq__(self, other):
        return other is not None and \
               self.name == other.name and \
               self.iter_function == other.iter_function

    def __neq(self, other):
        return other is None or \
               self.name != other.name or \
               self.iter_function != other.iter_function

    def __str__(self) -> str:
        return f"Generator<{self.iter_function.func_name}>"

    def __hash__(self):
        return hash(f"Generator<{self.iter_function.func_name}, " +
                    f"{self.iter_function.args}>")

    def get_iter_return(self, loc):
        return self.typ

    def iter_condition(self, func, self_ptr, loc):
        continue_ptr = func.builder.gep(self_ptr,
                                        [ir.Constant(ir.IntType(32), 0),
                                         ir.Constant(ir.IntType(32), 0)])
        return func.builder.load(continue_ptr)

    def iter(self, func, self_ptr, loc):
        func.builder.call(self.iter_function.yield_function, (self_ptr,))
        value_ptr = func.builder.gep(self_ptr,
                                     [ir.Constant(ir.IntType(32), 0),
                                      ir.Constant(ir.IntType(32), 2)])
        value = func.builder.load(value_ptr)
        return value

    def iter_get_val(self, func, self_ptr, loc):
        return self.iter(func, self_ptr, loc)
