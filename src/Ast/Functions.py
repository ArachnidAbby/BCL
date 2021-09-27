from llvmlite import ir
import Errors

class StandardFunction():
    def __init__(self, program, printf, value, lineno):
        self.builder = program.builder
        self.module = program.module
        self.printf = printf
        self.args = value
        self.program = program
        self.lineno = lineno

    def eval(self):
        if len(self.args)>self.argNum:
            Errors.Error.Invalid_Arguement_Count(self.lineno,len(self.args), self.argNum)

class Print(StandardFunction):
    def eval(self):
        self.argNum = 1
        super().eval()
        #print(self.value)
        value = self.args.eval()[0]

        # Declare argument list
        voidptr_ty = ir.IntType(8).as_pointer()
        
        fmt_arg = self.builder.bitcast(self.program.global_fmt_int, voidptr_ty)

        # Call Print Function
        self.builder.call(self.printf, [fmt_arg, value])

class Println(StandardFunction):
    def eval(self):
        self.argNum = 1
        super().eval()
        #print(self.value)
        value = self.args.eval()[0]

        # Declare argument list
        voidptr_ty = ir.IntType(8).as_pointer()
        if self.args.stuff[0].type=="number":
            #fmt_arg = self.builder.bitcast(self.program.global_fmt_int_n, voidptr_ty)
            self.builder.call(self.printf, [self.program.fmt_int_n,value])
        else:
            self.builder.call(self.printf, [self.program.fmt_string_n,value])