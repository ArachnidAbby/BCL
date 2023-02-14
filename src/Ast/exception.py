from llvmlite import ir  # type: ignore

import errors
from Ast.functions import standardfunctions


# TODO: MAKE BETTER
def over_index_exception(func, name, index, pos):
    over_index_fmt = (f"{errors.RED}Invalid index '%i' for array" +
                      f" '{str(name)}'\n\tLine: {pos[0]}{errors.RESET} \n\0")
    formatted_str = over_index_fmt.encode("utf8")
    c_over_index_fmt = ir.Constant(ir.ArrayType(ir.IntType(8),
                                                len(over_index_fmt)),
                                   bytearray(formatted_str))
    err_str = func.builder.alloca(ir.ArrayType(ir.IntType(8),
                                               len(over_index_fmt)))
    fmt_bitcast = func.builder.bitcast(err_str, ir.IntType(8).as_pointer())
    func.builder.store(c_over_index_fmt, err_str)
    func.builder.call(standardfunctions.printf, [fmt_bitcast, index])
    func.builder.call(standardfunctions.exit_func,
                      [ir.Constant(ir.IntType(32), 1)])
