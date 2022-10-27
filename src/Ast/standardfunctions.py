
from llvmlite import ir

from Ast import Ast_Types

from . import function

# ! This whole module should eventually be removed.
# !     It is temporary while certain aspects of the language are still in developement

printf = None

fmt = "%i \n\0"
c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                    bytearray(fmt.encode("utf8")))
gpistr = None

voidptr_ty = ir.IntType(8).as_pointer()

# todo: make this more readable!
def declare_printf(module):
    global printf, gpistr
    
    printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
    printf = ir.Function(module, printf_ty, name="printf")
    function.functions["__printf"] = [printf,'void']

    fmt = "%i \n\0"
    c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                        bytearray(fmt.encode("utf8")))
    gpistr = ir.GlobalVariable(module, c_fmt.type, name="fstr_int_n")
    gpistr.linkage = 'internal'
    gpistr.initializer = c_fmt
    gpistr.global_constant = True

@function.internal_function("println", Ast_Types.Integer_32(), (Ast_Types.Integer_32(),))
def std_println_int(func, args):
    x = args[0]
    pistr = func.builder.bitcast(gpistr, voidptr_ty)
    return func.builder.call(printf, [pistr, x])

# LLVM functions made accessible to users below
#   this is all just functionality not usually afforded so `add`, `sub`, etc. will not be provided

## ----Integer operations------
@function.internal_function("ll_shl", Ast_Types.Void(), (Ast_Types.Integer_32(), Ast_Types.Integer_32()))
def llvm_exposed_shl(func, args):
    return func.builder.shl(args[0], args[1])

@function.internal_function("ll_lshr", Ast_Types.Void(), (Ast_Types.Integer_32(), Ast_Types.Integer_32()))
def llvm_exposed_lshr(func, args):
    return func.builder.lshr(args[0], args[1])

@function.internal_function("ll_ashr", Ast_Types.Void(), (Ast_Types.Integer_32(), Ast_Types.Integer_32()))
def llvm_exposed_ashr(func, args):
    return func.builder.ashr(args[0], args[1])

@function.internal_function("ll_cttz", Ast_Types.Void(), (Ast_Types.Integer_32(), Ast_Types.Integer_1()))
def llvm_exposed_cttz(func, args):
    return func.builder.cttz(args[0], args[1])

@function.internal_function("ll_ctlz", Ast_Types.Void(), (Ast_Types.Integer_32(), Ast_Types.Integer_1()))
def llvm_exposed_ctlz(func, args):
    return func.builder.ctlz(args[0], args[1])

@function.internal_function("ll_neg", Ast_Types.Void(), (Ast_Types.Integer_32(), ))
def llvm_exposed_neg(func, args):
    return func.builder.neg(args[0])

@function.internal_function("ll_urem", Ast_Types.Void(), (Ast_Types.Integer_32(), Ast_Types.Integer_32()))
def llvm_exposed_urem(func, args):
    return func.builder.nurem(args[0], args[0])
