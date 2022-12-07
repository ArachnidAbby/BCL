
from llvmlite import ir

from Ast import Ast_Types

from . import function

printf = None
exit_func = None
sleep_func = None
usleep_func = None


fmt_strings = {"nl":{}, "nonl":{}}

voidptr_ty = ir.IntType(8).as_pointer()


def declare_global_str(module, inp: str, name: str):
    fmt = inp
    c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                        bytearray(fmt.encode("utf8")))
    out = ir.GlobalVariable(module, c_fmt.type, name=name)
    out.linkage = 'internal'
    out.initializer = c_fmt  # type: ignore
    out.global_constant = True
    return out

# todo: make this more readable!
def declare_printf(module):
    global printf, fmt_strings
    
    printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
    printf = ir.Function(module, printf_ty, name="printf")
    function.functions["__printf"] = [printf,'void']


    fmt_strings["nl"]["i32"] = declare_global_str(module, "%i\n\0", "fstr_int_n")
    fmt_strings["nonl"]["i32"] = declare_global_str(module, "%i\0", "fstr_int")
    fmt_strings["nl"]["char"] = declare_global_str(module, "%c\n\0", "fstr_char_n")
    fmt_strings["nonl"]["char"] = declare_global_str(module, "%c\0", "fstr_char")
    fmt_strings["nl"]["str"] = declare_global_str(module, "%s\n\0", "fstr_str_n")
    fmt_strings["nonl"]["str"] = declare_global_str(module, "%s\0", "fstr_str")
    fmt_strings["nl"]["bool"] = declare_global_str(module, "%d\n\0", "fstr_bool_n")
    fmt_strings["nonl"]["bool"] = declare_global_str(module, "%d\0", "fstr_bool")
    fmt_strings["nl"]["f32"] = declare_global_str(module, "%f\n\0", "fstr_float_n")
    fmt_strings["nonl"]["f32"] = declare_global_str(module, "%f\0", "fstr_float")

def declare_exit(module):
    global exit_func
    exit_ty = ir.FunctionType(ir.VoidType(), [ir.IntType(32)])
    exit_func = ir.Function(module, exit_ty, name="exit")

def declare_sleep(module):
    global sleep_func
    sleep_ty = ir.FunctionType(ir.VoidType(), [ir.IntType(32)])
    sleep_func = ir.Function(module, sleep_ty, name="sleep")

def declare_usleep(module):
    global usleep_func
    usleep_ty = ir.FunctionType(ir.VoidType(), [ir.IntType(32)])
    usleep_func = ir.Function(module, usleep_ty, name="usleep")


def declare_all(module):
    declare_printf(module)
    declare_exit(module)
    declare_sleep(module)
    declare_usleep(module)


@function.internal_function("println", Ast_Types.Integer_32(), (Ast_Types.Integer_32(),))
def std_println_int(func, args):
    x = args[0]
    pistr = func.builder.bitcast(fmt_strings["nl"]["i32"], voidptr_ty)
    return func.builder.call(printf, [pistr, x])

@function.internal_function("print", Ast_Types.Integer_32(), (Ast_Types.Integer_32(),))
def std_print_int(func, args):
    x = args[0]
    pistr = func.builder.bitcast(fmt_strings["nonl"]["i32"], voidptr_ty)
    return func.builder.call(printf, [pistr, x])

@function.internal_function("println", Ast_Types.Integer_32(), (Ast_Types.Char(),))
def std_println_char(func, args):
    x = args[0]
    pistr = func.builder.bitcast(fmt_strings["nl"]["char"], voidptr_ty)
    return func.builder.call(printf, [pistr, x])

@function.internal_function("print", Ast_Types.Integer_32(), (Ast_Types.Char(),))
def std_print_char(func, args):
    x = args[0]
    pistr = func.builder.bitcast(fmt_strings["nonl"]["char"], voidptr_ty)
    return func.builder.call(printf, [pistr, x])

@function.internal_function("println", Ast_Types.Integer_32(), (Ast_Types.StringLiteral(None),))
def std_println_str(func, args):
    x = args[0]
    pistr = func.builder.bitcast(fmt_strings["nl"]["str"], voidptr_ty)
    return func.builder.call(printf, [pistr, x])

@function.internal_function("print", Ast_Types.Integer_32(), (Ast_Types.StringLiteral(None),))
def std_print_str(func, args):
    x = args[0]
    pistr = func.builder.bitcast(fmt_strings["nonl"]["str"], voidptr_ty)
    return func.builder.call(printf, [pistr, x])

@function.internal_function("println", Ast_Types.Integer_32(), (Ast_Types.Integer_1(),))
def std_println_bool(func, args):
    x = args[0]
    pistr = func.builder.bitcast(fmt_strings["nl"]["bool"], voidptr_ty)
    return func.builder.call(printf, [pistr, x])

@function.internal_function("print", Ast_Types.Integer_32(), (Ast_Types.Integer_1(),))
def std_print_bool(func, args):
    x = args[0]
    pistr = func.builder.bitcast(fmt_strings["nonl"]["bool"], voidptr_ty)
    return func.builder.call(printf, [pistr, x])

@function.internal_function("println", Ast_Types.Integer_32(), (Ast_Types.Float_32(),))
def std_println_f32(func, args):
    x = args[0]
    pistr = func.builder.bitcast(fmt_strings["nl"]["f32"], voidptr_ty)
    return func.builder.call(printf, [pistr, x])

@function.internal_function("print", Ast_Types.Integer_32(), (Ast_Types.Float_32(),))
def std_print_f32(func, args):
    x = args[0]
    pistr = func.builder.bitcast(fmt_strings["nonl"]["f32"], voidptr_ty)
    return func.builder.call(printf, [pistr, x])



@function.internal_function("exit", Ast_Types.Void(), (Ast_Types.Integer_32(),))
def std_exit(func, args):
    return func.builder.call(exit_func, args)

@function.internal_function("sleep", Ast_Types.Void(), (Ast_Types.Integer_32(),))
def std_sleep(func, args):
    return func.builder.call(sleep_func, args)

@function.internal_function("usleep", Ast_Types.Void(), (Ast_Types.Integer_32(),))
def std_usleep(func, args):
    return func.builder.call(usleep_func, args)


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
