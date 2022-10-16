
from llvmlite import ir

from Ast import Ast_Types


from . import Function

# ! This whole module should eventually be removed.
# !     It is temporary while certain aspects of the language are still in developement

printf = None

fmt = "%i \n\0"
c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                    bytearray(fmt.encode("utf8")))
gpistr = None

voidptr_ty = ir.IntType(8).as_pointer()

def declare_printf(module):
    global printf, gpistr
    
    printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
    printf = ir.Function(module, printf_ty, name="printf")
    Function.functions["__printf"] = [printf,'void']

    fmt = "%i \n\0"
    c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                        bytearray(fmt.encode("utf8")))
    gpistr = ir.GlobalVariable(module, c_fmt.type, name="fstr_int_n")
    gpistr.linkage = 'internal'
    gpistr.initializer = c_fmt
    gpistr.global_constant = True

@Function.internal_function("println", Ast_Types.Integer_32(), (Ast_Types.Integer_32(),))
def std_println_int(func, args):
    x = args[0]
    pistr = func.builder.bitcast(gpistr, voidptr_ty)
    return func.builder.call(printf, [pistr, x])
