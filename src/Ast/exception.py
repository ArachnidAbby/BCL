from pathlib import Path

from llvmlite import ir

import errors
from Ast.Ast_Types.Type_I32 import Integer_32  # type: ignore
from Ast.literals import stringliteral
from Ast.nodes.commontypes import SrcPosition
from Ast.nodes.parenthese import ParenthBlock
from Ast.variables.reference import VariableRef

PRINTF_ARGS = ()
EXIT_ARGS = (Integer_32(),)


def _get_function(func, name: str, args: tuple, pos):
    function = func.module.get_global(name)
    if function is None:
        errors.error(f"Could not get function {name}, hint: import stdlib",
                     line=pos)
    function = function.obj
    args_fixed = ParenthBlock(pos)
    for arg in args:
        args_fixed.children.append(arg)
    return function.get_function(func, VariableRef(pos, name, None),
                                 args_fixed)


# TODO: MAKE BETTER
def over_index_exception(func, name, index, pos):
    from Ast.Ast_Types import definedtypes
    from Ast.module import base_package
    strlit_ty = definedtypes.types_dict["strlit"]

    location = Path(pos[3]).relative_to(base_package.location)

    over_index_fmt = (f"{errors.RED}Invalid index '%i' for array" +
                      f"\n    File: {location}:{pos[0]}:{pos[1]}{errors.RESET}\n")

    fmt_bitcast = stringliteral.StrLiteral(pos, over_index_fmt)

    printf_args = (strlit_ty, Integer_32())
    exit_args = (Integer_32(),)

    printf = _get_function(func, "printf", printf_args, pos)
    exit_func = _get_function(func, "exit", exit_args, pos)

    func.builder.call(printf.func_obj, [fmt_bitcast.eval(func), index])
    func.builder.call(exit_func.func_obj,
                      [ir.Constant(ir.IntType(32), 1)])


def no_next_item(func, name):
    from Ast.Ast_Types import definedtypes
    error_fmt = (f"{errors.RED}No next item available" +
                 f" '{str(name)}'\n\tLine: N/A{errors.RESET} \n")
    strlit_ty = definedtypes.types_dict["strlit"]

    fmt_bitcast = stringliteral.StrLiteral(SrcPosition.invalid(),
                                           error_fmt)

    printf_args = (strlit_ty, Integer_32())
    exit_args = (Integer_32(),)

    printf = _get_function(func, "printf", printf_args, SrcPosition.invalid())
    exit_func = _get_function(func, "exit", exit_args, SrcPosition.invalid())

    func.builder.call(printf.func_obj, [fmt_bitcast.eval(func)])
    func.builder.call(exit_func.func_obj,
                      [ir.Constant(ir.IntType(32), 2)])


def slice_size_exception(func, name, slice_size, array_size: int, pos):
    from Ast.Ast_Types import definedtypes
    from Ast.module import base_package
    strlit_ty = definedtypes.types_dict["strlit"]

    location = Path(pos[3]).relative_to(base_package.location)

    error_fmt = (f"{errors.RED}Slice too small: '%i' size must be " +
                 f">= {array_size} '{str(name)}'\n" +
                 f"    File: {location}:{pos[0]}:{pos[1]}{errors.RESET}\n")

    fmt_bitcast = stringliteral.StrLiteral(pos, error_fmt)

    printf_args = (strlit_ty, Integer_32())
    exit_args = (Integer_32(),)

    printf = _get_function(func, "printf", printf_args, pos)
    exit_func = _get_function(func, "exit", exit_args, pos)

    func.builder.call(printf.func_obj, [fmt_bitcast.eval(func), slice_size])
    func.builder.call(exit_func.func_obj,
                      [ir.Constant(ir.IntType(32), 1)])


def impossible_union_cast(func, tag, correct_typ, typ_list, pos):
    from Ast.Ast_Types import definedtypes
    from Ast.module import base_package
    location = Path(pos[3]).relative_to(base_package.location)

    error_fmt = (f"{errors.RED}Union type cast failed\n" +
                 f"  expect: {correct_typ.__str__()}\n" +
                 "  got: %s" +
                 f"\n    File: {location}:{pos[0]}:{pos[1]}{errors.RESET}\n")
    strlit_ty = definedtypes.types_dict["strlit"]

    fmt_bitcast = stringliteral.StrLiteral(SrcPosition.invalid(),
                                           error_fmt)

    printf_args = (strlit_ty, strlit_ty)
    exit_args = (Integer_32(),)

    printf = _get_function(func, "printf", printf_args, SrcPosition.invalid())
    exit_func = _get_function(func, "exit", exit_args, SrcPosition.invalid())

    block_name = func.builder.block.name
    default_branch = func.builder.append_basic_block(block_name + ".unreachable")
    switch_stmt = func.builder.switch(tag, default_branch)
    func.builder.position_at_start(default_branch)
    func.builder.unreachable()

    for c, typ in enumerate(typ_list):
        if typ == correct_typ:
            continue
        typ_name = stringliteral.StrLiteral(SrcPosition.invalid(),
                                            typ.__str__())
        new_br = func.builder.append_basic_block()
        bad_tag = ir.Constant(ir.IntType(32), c)
        func.builder.position_at_start(new_br)
        func.builder.call(printf.func_obj, [fmt_bitcast.eval(func),
                                            typ_name.eval(func)])
        func.builder.call(exit_func.func_obj,
                          [ir.Constant(ir.IntType(32), 4)])
        switch_stmt.add_case(bad_tag, new_br)
