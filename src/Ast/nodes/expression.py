import Ast.Ast_Types as Ast_Types
from Ast.nodes.astnode import ASTNode
from Ast.nodes.commontypes import SrcPosition
from errors import error


class ExpressionNode(ASTNode):
    '''Acts as an Expression in the AST.
    This means it has a value and return type'''
    __slots__ = ("ret_type", "ir_type", "ptr")

    def __init__(self, position: SrcPosition, *args, **kwargs):
        self.ret_type = Ast_Types.Type()
        self._position = position
        self.ptr = None
        super().__init__(position, *args, **kwargs)

    def get_ptr(self, func):
        '''allocate to stack and get a ptr'''
        if self.ptr is None:
            self.ptr = func.create_const_var(self.ret_type)
            val = self.eval(func)
            func.builder.store(val, self.ptr)
        return self.ptr

    def as_type_reference(self, func):
        '''Get this expresion as the reference to a type'''
        error(f"invalid type: {str(self)}", line=self.position)
