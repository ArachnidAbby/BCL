from llvmlite import ir

import errors
from Ast import Ast_Types  # type: ignore
from Ast.functions import standardfunctions
from Ast.literals import stringliteral
from Ast.nodes.commontypes import SrcPosition
from Ast.nodes.parenthese import ParenthBlock
from Ast.variables.reference import VariableRef

PRINTF_ARGS = ()
EXIT_ARGS = (Ast_Types.Integer_32(),)


def _get_function(module, name: str, args: tuple, pos):
    func = module.get_global(name)
    if func is None:
        errors.error(f"Could not get function {name}, hint: import stdlib",
                     line=pos)
    args_fixed = ParenthBlock(pos)
    for arg in args:
        args_fixed.children.append(arg)
    return func.get_function(VariableRef(pos, name, None), args_fixed)


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

    printf_args = (Ast_Types.StringLiteral(), Ast_Types.Integer_32())
    exit_args = (Ast_Types.Integer_32(),)

    printf = _get_function(func.module, "printf", printf_args, pos)
    exit_func = _get_function(func.module, "exit", exit_args, pos)

    func.builder.call(printf.func_obj, [fmt_bitcast.eval(func), index])
    func.builder.call(exit_func.func_obj,
                      [ir.Constant(ir.IntType(32), 1)])
