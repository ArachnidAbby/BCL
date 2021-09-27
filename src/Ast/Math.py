class BinaryOp():
    def __init__(self, program, left, right):
        self.builder = program.builder
        self.module = program.module
        self.left = left
        self.right = right
        self.type = "number"


class Sum(BinaryOp):
    def eval(self):
        i = self.builder.add(self.left.eval(), self.right.eval())
        return i


class Sub(BinaryOp):
    def eval(self):
        i = self.builder.sub(self.left.eval(), self.right.eval())
        return i