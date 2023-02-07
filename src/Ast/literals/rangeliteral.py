class RangeLiteral(ExpressionNode):
    __slots__ = ('start', 'end')
    # name = 'literal'

    def __init__(self, pos: SrcPosition, start: Any, end: Any):
        super().__init__(pos)
        self.start = start
        self.end = end
    
    def pre_eval(self, func):
        self.start.pre_eval(func)
        self.end.pre_eval(func)

    def eval(self, func):
        self.start = self.start.eval(func)
        self.end = self.end.eval(func)

    @property
    def position(self) -> tuple[int, int, int]:
        return self.merge_pos((self.start.position, self.end.position))