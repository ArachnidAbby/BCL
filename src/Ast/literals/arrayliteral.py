class ArrayLiteral(ExpressionNode): # TODO: REFACTOR
    __slots__ = ('value', 'ir_type', 'literal')
    # name = 'literal'

    def __init__(self, pos: SrcPosition, value: list[Any]):
        super().__init__(pos)
        self.value = value
        self.ptr = None
        self.literal = True # whether or not this array is only full of literals
        
    def pre_eval(self, func):
        self.value[0].pre_eval(func)
        typ = self.value[0].ret_type

        for x in self.value:
            x.pre_eval(func)
            if x.ret_type!=typ:
                errors.error(f"Invalid type '{x.ret_type}' in a list of type '{typ}'", line = x.position)
            if x.name!='literal':
                self.literal = False
            

        array_size  = Literal((-1,-1,-1), len(self.value), Ast_Types.Integer_32)
        self.ret_type = Ast_Types.Array(array_size, typ)
        self.ir_type = self.ret_type.ir_type

    def eval(self, func):
        if not self.literal:
            ptr = func.create_const_var(self.ret_type)
            zero_const = ir.Constant(ir.IntType(64), 0)
            for c, item in enumerate(self.value):
                index = ir.Constant(ir.IntType(32), c)
                item_ptr = func.builder.gep(ptr , [zero_const, index])
                func.builder.store(item.eval(func), item_ptr)
            self.ptr = ptr
            return func.builder.load(ptr)
        
        return ir.Constant.literal_array([x.eval(func) for x in self.value])
    
    @property
    def position(self) -> tuple[int, int, int]:
        x = list(self.merge_pos([x.position for x in self.value]))  # type: ignore
        return (x[0], x[1], x[2]+1)