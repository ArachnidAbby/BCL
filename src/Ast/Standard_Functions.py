from llvmlite import ir

from . import Function


printf = None

def declare_printf(module):
    global printf
    voidptr_ty = ir.IntType(8).as_pointer()
    printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
    printf = ir.Function(module, printf_ty, name="printf")
    Function.functions["__printf"] = printf

    fmt = "%i \n\0"
    c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                        bytearray(fmt.encode("utf8")))
    gpistr = ir.GlobalVariable(module, c_fmt.type, name="fstr_int_n")
    gpistr.linkage = 'internal'
    gpistr.initializer = c_fmt
    gpistr.global_constant = True
    
    int_ty = ir.IntType(32)
    printint_ty = ir.FunctionType(ir.IntType(32), [int_ty])
    printint = ir.Function(module, printint_ty, name="print_int")

    block = printint.append_basic_block(name="entry")
    builder = ir.IRBuilder(block)
    x = printint.args[0]
    pistr = builder.bitcast(gpistr, voidptr_ty)
    s = builder.call(printf, [pistr, x])
    builder.ret(s)
    
    # print("E::",
    #     x,
    #     int_ty,
    #     printint_ty,
    #     x,
    #     fmt,
    #     c_fmt,
    #     gpistr,
    #     block,
    #     builder,
    #     printint,
    #     sep = "\n|"
    # )

    
    Function.functions["print_int"] = [printint, "void"]



# from llvmlite import ir
# import Errors

# class StandardFunction():
#     def __init__(self, program, printf, value, lineno):
#         self.builder = program.builder
#         self.module = program.module
#         self.printf = printf
#         self.args = value
#         self.program = program
#         self.lineno = lineno

#     def eval(self):
#         if len(self.args)>self.argNum:
#             Errors.Error.Invalid_Arguement_Count(self.lineno,len(self.args), self.argNum)

# class Print(StandardFunction):
#     def eval(self):
#         self.argNum = 1
#         super().eval()
#         #print(self.value)
#         value = self.args.eval()[0]

#         # Declare argument list
#         voidptr_ty = ir.IntType(8).as_pointer()
        
#         fmt_arg = self.builder.bitcast(self.program.global_fmt_int, voidptr_ty)

#         # Call Print Function
#         self.builder.call(self.printf, [fmt_arg, value])
