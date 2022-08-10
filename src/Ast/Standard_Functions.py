
from llvmlite import ir

from . import Function

# ! This whole module should eventually be removed.
# !     It is temporary while certain aspects of the language are still in developement

printf = None

def declare_printf(module):
    global printf
    voidptr_ty = ir.IntType(8).as_pointer()
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
    
    int_ty = ir.IntType(32)
    printint_ty = ir.FunctionType(ir.IntType(32), [int_ty])
    printint = ir.Function(module, printint_ty, name="print_int")

    block = printint.append_basic_block(name="entry")
    builder = ir.IRBuilder(block)
    x = printint.args[0]
    pistr = builder.bitcast(gpistr, voidptr_ty)
    s = builder.call(printf, [pistr, x])
    builder.ret(s)

    Function.functions["println"] = {}
    Function.functions["println"][('i32',)] = [printint, "void"]
