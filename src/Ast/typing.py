'''
Common types for stuff that would be seen as a
circular import when annotating normally
'''

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Ast.Ast_Types.Type_Base import Type
    from Ast.functions.definition import FunctionDef
    from Ast.module import Module
    from Ast.nodes.block import Block
    from Ast.variables.varobject import VariableObj
else:
    from typing import Any
    type Module = Any
    type Block = Any
    type FunctionDef = Any
    type VariableObj = Any
    type Type = Any

__all__ = ["Module", "Block", "FunctionDef", "VariableObj", "Type"]
