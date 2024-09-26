import Ast.Ast_Types as Ast_Types
from Ast.nodes.astnode import ASTNode
from Ast.nodes.block import create_const_var, get_current_block
from Ast.nodes.commontypes import Lifetimes, SrcPosition
from errors import error


class ExpressionNode(ASTNode):
    '''Acts as an Expression in the AST.
    This means it has a value and return type'''
    __slots__ = ("ret_type", "ptr", '__evaled', 'overwrite_eval')
    do_register_dispose = True

    def __init__(self, position: SrcPosition, *args, **kwargs):
        self.ret_type = Ast_Types.Type()
        self._position = position
        self.ptr = None
        self.__evaled = False
        self.overwrite_eval = False
        super().__init__(position, *args, **kwargs)

    def copy(self):
        return self

    def get_ptr(self, func):
        '''allocate to stack and get a ptr'''
        if self.ptr is None:
            self.ptr = create_const_var(func, self.ret_type)
            val = self.eval(func)
            # self._instruction = val
            func.builder.store(val, self.ptr)
        return self.ptr

    def fullfill_templates(self, func):
        return super().fullfill_templates(func)

    def eval(self, func, *args, **kwargs):
        if self.do_register_dispose and self.ret_type is not None and \
                self.ret_type.needs_dispose and \
                not self.__evaled and not self.overwrite_eval:
            self.__evaled = True
            self.get_ptr(func)
            self.__evaled = False

            block = get_current_block()
            block.register_dispose(func, self)
            if self._instruction is None:
                self._instruction = self.eval_impl(func, *args, **kwargs)
        else:
            self._instruction = self.eval_impl(func, *args, **kwargs)

        self.__evaled = True

        return self._instruction

    def get_var(self, func):
        '''Place holder!
        Useful when we want something to act like a variable.
        The default is to have something return itself.
        '''
        return self

    # @abstractmethod
    def get_lifetime(self, func) -> Lifetimes:
        return Lifetimes.UNKNOWN

    def get_coupled_lifetimes(self, func) -> list:
        '''Used in a few circumstances to get arguments that need to
        have their lifetimes coupled together.'''
        return []

    def store(self, func, ptr, value,
              typ, first_assignment=False):
        '''Store data at some address '''
        self.ret_type.assign(func, ptr, value, typ,
                             first_assignment=first_assignment)

    def reset(self):
        super().reset()
        self.ptr = None
        self.__evaled = False
        self.overwrite_eval = False

    def get_value(self, func):
        return self

    def as_type_reference(self, func, allow_generics=False):
        '''Get this expresion as the reference to a type'''
        error("invalid type name:", line=self.position)

    def get_const_value(self) -> int | float:
        return 0

    @property
    def is_constant_expr(self) -> bool:
        return False

    @property
    def ir_type(self):
        return self.ret_type.ir_type
