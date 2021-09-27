from . import Type
from llvmlite import ir

class Byte_8(Type.Type):
    def __init__(self, value, program):
        self.program = program
        functionList ={}

        super().__init__("byte", value, functionList, None)

    def eval(self):
        i = ir.Constant(ir.IntType(8), int(self.value))
        return i

class Short_16(Type.Type):
    def __init__(self, value, program):
        self.program = program
        functionList ={}

        super().__init__("short", value, functionList, None)

    def eval(self):
        i = ir.Constant(ir.IntType(16), int(self.value))
        return i

class Int_32(Type.Type):
    def __init__(self, value, program):
        self.program = program
        functionList ={}

        super().__init__("int", value, functionList, None)
        self.type = "number"

    def eval(self):
        i = ir.Constant(ir.IntType(32), int(self.value))
        return i

class Long_64(Type.Type):
    def __init__(self, value, program):
        self.program = program
        functionList ={}

        super().__init__("long", value, functionList, None)

    def eval(self):
        i = ir.Constant(ir.IntType(64), int(self.value))
        return i
