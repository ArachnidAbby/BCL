from llvmlite import ir

from Ast.Ast_Types.Type_Base import Type


class GeneratorType(Type):
    __slots__ = ("iter_function", "ir_type", "typ")

    is_iterator = True
    name = "Generator"

    def __init__(self, iter_function, typ):
        self.iter_function = iter_function
        self.typ = typ
        # {continue: i1, state: i8*, result: typ, ...}
        self.ir_type = ir.global_context.get_identified_type(f"struct.{iter_function.func_name}")

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

    def get_iter_return(self):
        return self.typ

    def iter_condition(self, func, self_ptr):
        continue_ptr = func.builder.gep(self_ptr,
                                        [ir.Constant(ir.IntType(32), 0),
                                         ir.Constant(ir.IntType(32), 0)])
        return func.builder.load(continue_ptr)

    def iter(self, func, self_ptr):
        func.builder.call(self.iter_function.yield_function, (self_ptr,))
        value_ptr = func.builder.gep(self_ptr,
                                     [ir.Constant(ir.IntType(32), 0),
                                      ir.Constant(ir.IntType(32), 2)])
        value = func.builder.load(value_ptr)
        return value

    def iter_get_val(self, func, self_ptr):
        return self.iter(func, self_ptr)
