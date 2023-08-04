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


def _get_function(func, name: str, args: tuple, pos):
    function = func.module.get_global(name)
    if function is None:
        errors.error(f"Could not get function {name}, hint: import stdlib",
                     line=pos)
    args_fixed = ParenthBlock(pos)
    for arg in args:
        args_fixed.children.append(arg)
    return function.get_function(func, VariableRef(pos, name, None), args_fixed)


# TODO: MAKE BETTER
def over_index_exception(func, name, index, pos):
    from Ast.Ast_Types import definedtypes
    strlit_ty = definedtypes.types_dict["strlit"]

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

    printf_args = (strlit_ty, Ast_Types.Integer_32())
    exit_args = (Ast_Types.Integer_32(),)

    printf = _get_function(func, "printf", printf_args, pos)
    exit_func = _get_function(func, "exit", exit_args, pos)

    func.builder.call(printf.func_obj, [fmt_bitcast.eval(func), index])
    func.builder.call(exit_func.func_obj,
                      [ir.Constant(ir.IntType(32), 1)])


def no_next_item(func, name):
    from Ast.Ast_Types import definedtypes
    over_index_fmt = (f"{errors.RED}No next item available" +
                      f" '{str(name)}'\n\tLine: N/A{errors.RESET} \n")
    strlit_ty = definedtypes.types_dict["strlit"]

    fmt_bitcast = stringliteral.StrLiteral(SrcPosition.invalid(), over_index_fmt)

    printf_args = (strlit_ty, Ast_Types.Integer_32())
    exit_args = (Ast_Types.Integer_32(),)

    printf = _get_function(func, "printf", printf_args, SrcPosition.invalid())
    exit_func = _get_function(func, "exit", exit_args, SrcPosition.invalid())

    func.builder.call(printf.func_obj, [fmt_bitcast.eval(func)])
    func.builder.call(exit_func.func_obj,
                      [ir.Constant(ir.IntType(32), 2)])
