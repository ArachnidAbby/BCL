class StructLiteral(ExpressionNode): # TODO REMOVE UNUSED CODE IN COMMENTS
    __slots__ = ('members',)
    # name = 'literal'

    def __init__(self, pos: SrcPosition, name, members: Block):
        super().__init__(pos)
        self.members = members
        self.ret_type = name.as_type_reference()
    
    def pre_eval(self, func):
        # if not isinstance(self.members.children[0], ContainerNode):
        #     errors.error("Invalid Syntax:", line = self.members.position)
        self.members.pre_eval(func);
        for child in self.members:
            if not isinstance(child, KeyValuePair):
                errors.error("Invalid Syntax:", line = child.position)
            child.value.pre_eval(func)

    def eval(self, func):
        ptr = func.create_const_var(self.ret_type)
        zero_const = ir.Constant(ir.IntType(64), 0)
        idx_lookup = {name: idx for idx, name in enumerate(self.ret_type.member_indexs)}
        for child in self.members:
            index = ir.Constant(ir.IntType(32), idx_lookup[child.key.var_name])
            item_ptr = func.builder.gep(ptr , [zero_const, index])
            func.builder.store(child.value.eval(func), item_ptr)
        self.ptr = ptr
        return func.builder.load(ptr)

    # @property
    # def position(self) -> tuple[int, int, int]:
    #     return self.merge_pos((self.start.position, self.end.position))