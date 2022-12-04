
from llvmlite import ir

from Ast import Ast_Types

from . import function

printf = None
exit_func = None

fmt = "%i \n\0"
c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                    bytearray(fmt.encode("utf8")))
gpistr = None
gpistr2 = None

voidptr_ty = ir.IntType(8).as_pointer()

# todo: make this more readable!
def declare_printf(module):
    global printf, gpistr, gpistr2
    
    printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
    printf = ir.Function(module, printf_ty, name="printf")
    function.functions["__printf"] = [printf,'void']

    fmt = "%i\n\0"
    c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                        bytearray(fmt.encode("utf8")))
    gpistr = ir.GlobalVariable(module, c_fmt.type, name="fstr_int_n")
    gpistr.linkage = 'internal'
    gpistr.initializer = c_fmt  # type: ignore
    gpistr.global_constant = True

    fmt = "%i\0"
    c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                        bytearray(fmt.encode("utf8")))
    gpistr2 = ir.GlobalVariable(module, c_fmt.type, name="fstr_int")
    gpistr2.linkage = 'internal'
    gpistr2.initializer = c_fmt  # type: ignore
    gpistr2.global_constant = True

def declare_exit(module):
    global exit_func
    exit_ty = ir.FunctionType(ir.VoidType(), [ir.IntType(32)])
    exit_func = ir.Function(module, exit_ty, name="exit")

@function.internal_function("println", Ast_Types.Integer_32(), (Ast_Types.Integer_32(),))
def std_println_int(func, args):
    x = args[0]
    pistr = func.builder.bitcast(gpistr, voidptr_ty)
    return func.builder.call(printf, [pistr, x])

@function.internal_function("print", Ast_Types.Integer_32(), (Ast_Types.Integer_32(),))
def std_print_int(func, args):
    x = args[0]
    pistr = func.builder.bitcast(gpistr2, voidptr_ty)
    return func.builder.call(printf, [pistr, x])

@function.internal_function("exit", Ast_Types.Void(), (Ast_Types.Integer_32(),))
def std_exit(func, args):
    return func.builder.call(exit_func, args)


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
