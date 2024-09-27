from llvmlite import ir

import errors
from Ast.Ast_Types.Type_Alias import Alias
from Ast.Ast_Types.Type_Base import Type
from Ast.Ast_Types.Type_Void import Void
from Ast.nodes.passthrough import PassNode

TAG_TYPE = ir.IntType(32)


class Union(Type):
    __slots__ = ("inner_types", "module")

    name = "UNION"
    pass_as_ptr = True

    def __init__(self, module, types):
        self.module = module
        self.inner_types = types

    @property
    def needs_dispose(self) -> bool:
        return any((x.needs_dispose for x in self.inner_types))

    @property
    def returnable(self) -> bool:
        return any((x.needs_dispose for x in self.inner_types))

    def __str__(self) -> str:
        return " | ".join([inner.__str__() for inner in self.inner_types])

    def __eq__(self, other) -> bool:
        if isinstance(other, Alias):
            return self.name == other.dealias().name \
                and other.dealias().inner_types == self.inner_types \

        return super().__eq__(other) \
            and other.inner_types == self.inner_types

    def __hash__(self):
        return hash("UNION--" + self.__str__())

    @property
    def ir_type(self) -> ir.Type:
        sizes = (t.get_abi_size(self.module) for t in self.inner_types)
        max_size = max(sizes)
        return ir.LiteralStructType((TAG_TYPE,
                                     ir.ArrayType(ir.IntType(8),
                                                  max_size)))

    def valid_inner_type(self, typ):
        for inner in self.inner_types:
            if inner == typ:
                return True
        return False

    def get_id_of_type(self, typ) -> int | None:
        for c, inner in enumerate(self.inner_types):
            if inner == typ:
                return c
        return None

    def convert_to(self, func, orig, typ):
        from Ast import exception
        if typ == self:
            return orig.eval(func)

        id = self.get_id_of_type(typ)
        if id is None:
            errors.error(f"Cannot convert {str(self)} to {typ.__str__()}",
                         line=orig.position)

        id_const = ir.Constant(TAG_TYPE, id)
        tag_ptr = func.builder.gep(orig.get_ptr(func),
                                   (ir.Constant(ir.IntType(64), 0),
                                    ir.Constant(ir.IntType(32), 0)))
        tag = func.builder.load(tag_ptr)
        tag_eq = func.builder.icmp_unsigned("==", tag, id_const)

        block_name = func.builder.block.name
        success_branch = func.builder.append_basic_block(block_name + ".union_cast_success")
        exit_branch = func.builder.append_basic_block(block_name + ".union_cast_fail")

        func.builder.cbranch(tag_eq, success_branch, exit_branch)
        func.builder.position_at_start(exit_branch)
        exception.impossible_union_cast(func, tag,
                                        typ, self.inner_types,
                                        orig.position)
        func.builder.unreachable()
        func.builder.position_at_start(success_branch)
        data_ptr_raw = func.builder.gep(orig.get_ptr(func),
                                        (ir.Constant(ir.IntType(64), 0),
                                         ir.Constant(ir.IntType(32), 1)))
        if not isinstance(typ, Void):
            data_ptr = func.builder.bitcast(data_ptr_raw, typ.ir_type.as_pointer())
            return func.builder.load(data_ptr)
        return ir.Undefined

    def convert_from(self, func, typ, orig):
        struct_ptr = self.instantiate_from(func, typ, orig)

        return func.builder.load(struct_ptr)

    def instantiate_from(self, func, typ, orig):
        id = self.get_id_of_type(typ)
        if id is None:
            errors.error(f"Cannot convert {typ.__str__()} to {str(self)}",
                         line=orig.position)

        struct_ptr = func.create_const_var(self)
        tag_ptr = func.builder.gep(struct_ptr,
                                   (ir.Constant(ir.IntType(64), 0),
                                    ir.Constant(ir.IntType(32), 0)))
        data_ptr_raw = func.builder.gep(struct_ptr,
                                        (ir.Constant(ir.IntType(64), 0),
                                         ir.Constant(ir.IntType(32), 1)))
        if not isinstance(orig.ret_type, Void):
            data_ptr = func.builder.bitcast(data_ptr_raw, typ.ir_type.as_pointer())
            func.builder.store(orig.eval(func), data_ptr)
        func.builder.store(ir.Constant(TAG_TYPE, id), tag_ptr)

        return struct_ptr

    def roughly_equals(self, func, other):
        '''check if two types are equivalent.
        This is helpful when you have compound types such as "Any"
        or a Protocol type.

        defaults to `__eq__` behavior
        '''
        return self == other or self.valid_inner_type(other)

    def runtime_roughly_equals_rev(self, func, obj, typ):
        '''check if two types are equivalent (at runtime).
        This is helpful when you have compound types such as "Any"
        or a Protocol type.

        defaults to `self.roughly_equals` behavior
        '''
        if typ == obj.ret_type:
            return ir.Constant(ir.IntType(1), 1)  # return True

        id = self.get_id_of_type(typ)
        if id is None:
            errors.warning(f"performing a runtime check for type: '{typ.__str__()}' " +
                           "will always be false",
                           line=obj.position)
            return ir.Constant(ir.IntType(1), 0)  # return False

        id_const = ir.Constant(TAG_TYPE, id)
        tag_ptr = func.builder.gep(obj.get_ptr(func),
                                   (ir.Constant(ir.IntType(64), 0),
                                    ir.Constant(ir.IntType(32), 0)))
        tag = func.builder.load(tag_ptr)
        return func.builder.icmp_unsigned("==", tag, id_const)

    def runtime_roughly_equals(self, func, obj):
        '''check if two types are equivalent (at runtime).
        This is helpful when you have compound types such as "Any"
        or a Protocol type.

        defaults to `self.roughly_equals` behavior
        '''
        return ir.Constant(ir.IntType(1), super().roughly_equals(func, obj))

    def pass_to(self, func, item):
        if item.ret_type == self:
            return super().pass_to(func, item)

        struct_ptr = self.instantiate_from(func, item.ret_type, item)
        # ! This needs to be loaded if "pass_by_ptr" is ever set to false
        return struct_ptr

    def add_ref_count(self, func, node):
        if not self.needs_dispose:
            return
        tag_ptr = func.builder.gep(node.get_ptr(func),
                                   (ir.Constant(ir.IntType(64), 0),
                                    ir.Constant(ir.IntType(32), 0)))
        tag = func.builder.load(tag_ptr)
        data_ptr_raw = func.builder.gep(node.get_ptr(func),
                                        (ir.Constant(ir.IntType(64), 0),
                                         ir.Constant(ir.IntType(32), 1)))

        block_name = func.builder.block.name
        default_branch = func.builder.append_basic_block(block_name + ".union.unreachable")
        after = func.builder.append_basic_block(block_name + ".union.after_addrefcount")
        switch_stmt = func.builder.switch(tag, default_branch)
        func.builder.position_at_start(default_branch)
        func.builder.unreachable()

        for c, typ in enumerate(self.inner_types):
            new_br = func.builder.append_basic_block()
            func.builder.position_at_start(new_br)
            data_ptr = func.builder.bitcast(data_ptr_raw,
                                            typ.ir_type.as_pointer())
            fake_node = PassNode(node.position,
                                 func.builder.load(data_ptr),
                                 typ, data_ptr)
            typ_tag = ir.Constant(ir.IntType(32), c)
            typ.add_ref_count(func, fake_node)
            func.builder.branch(after)
            switch_stmt.add_case(typ_tag, new_br)

        func.builder.position_at_start(after)

    def dispose(self, func, node):
        if not self.needs_dispose:
            return
        tag_ptr = func.builder.gep(node.get_ptr(func),
                                   (ir.Constant(ir.IntType(64), 0),
                                    ir.Constant(ir.IntType(32), 0)))
        tag = func.builder.load(tag_ptr)
        data_ptr_raw = func.builder.gep(node.get_ptr(func),
                                        (ir.Constant(ir.IntType(64), 0),
                                         ir.Constant(ir.IntType(32), 1)))

        block_name = func.builder.block.name
        default_branch = func.builder.append_basic_block(block_name + ".union.unreachable")
        after = func.builder.append_basic_block(block_name + ".union.after_dispose")
        switch_stmt = func.builder.switch(tag, default_branch)
        func.builder.position_at_start(default_branch)
        func.builder.unreachable()

        for c, typ in enumerate(self.inner_types):
            new_br = func.builder.append_basic_block()
            func.builder.position_at_start(new_br)
            data_ptr = func.builder.bitcast(data_ptr_raw,
                                            typ.ir_type.as_pointer())
            fake_node = PassNode(node.position,
                                 func.builder.load(data_ptr),
                                 typ, data_ptr)
            typ_tag = ir.Constant(ir.IntType(32), c)
            typ.dipose(func, fake_node)
            func.builder.branch(after)
            switch_stmt.add_case(typ_tag, new_br)

        func.builder.position_at_start(after)
        