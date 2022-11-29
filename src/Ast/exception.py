import errors
from llvmlite import ir

from Ast import Ast_Types, standardfunctions


def over_index_exception(func, name, index, pos):
    over_index_fmt = f"{errors.RED}Invalid index '%i' for array '{name}' \n\tLine: {pos[0]}{errors.RESET} \n\0"
    c_over_index_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(over_index_fmt)),
        bytearray(over_index_fmt.encode("utf8")))
    err_str = func.builder.alloca(ir.ArrayType(ir.IntType(8), len(over_index_fmt)))
    fmt_bitcast = func.builder.bitcast(err_str, ir.IntType(8).as_pointer())
    func.builder.store(c_over_index_fmt, err_str)
    func.builder.call(standardfunctions.printf, [fmt_bitcast, index])
    func.builder.call(standardfunctions.exit_func, [ir.Constant(Ast_Types.Integer_32.ir_type, 1)])
