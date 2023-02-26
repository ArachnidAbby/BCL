from llvmlite import ir

import errors
from Ast import Ast_Types  # type: ignore
from Ast.functions import standardfunctions
from Ast.literals import stringliteral

PRINTF_ARGS = ()
EXIT_ARGS = (Ast_Types.Integer_32(),)


# TODO: MAKE BETTER
def over_index_exception(func, name, index, pos):
    over_index_fmt = (f"{errors.RED}Invalid index '%i' for array" +
                      f" '{str(name)}'\n\tLine: {pos[0]}{errors.RESET} \n")
    # formatted_str = over_index_fmt.encode("utf8")
    # c_over_index_fmt = ir.Constant(ir.ArrayType(ir.IntType(8),
    #                                             len(over_index_fmt)),
    #                                bytearray(formatted_str))
    # err_str = func.builder.alloca(ir.ArrayType(ir.IntType(8),
    #                                            len(over_index_fmt)))
    # fmt_bitcast = func.builder.bitcast(err_str, ir.IntType(8).as_pointer())
    # func.builder.store(c_over_index_fmt, err_str)

    fmt_bitcast = stringliteral.StrLiteral(pos, over_index_fmt)

    printf_dict = func.module.get_function("printf", pos)
    printf = func.module.get_func_from_dict("printf", printf_dict,
                                            PRINTF_ARGS, pos)

    exit_dict = func.module.get_function("exit", pos)
    exit_func = func.module.get_func_from_dict("exit", exit_dict,
                                               EXIT_ARGS, pos)

    func.builder.call(printf.function_object, [fmt_bitcast.eval(func), index])
    func.builder.call(exit_func.function_object,
                      [ir.Constant(ir.IntType(32), 1)])
