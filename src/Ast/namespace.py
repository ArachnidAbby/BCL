from Ast import Ast_Types
from Ast.generics import GenericSpecify
from Ast.nodes.commontypes import SrcPosition
from Ast.nodes.expression import ExpressionNode
import errors


class NamespaceIndex(ExpressionNode):
    '''Index a namespace like this: `namespace::function``'''
    __slots__ = ("left", "right", "val", "star_idx")
    isconstant = True
    do_register_dispose = False

    def __init__(self, pos, left, right):
        super().__init__(pos)
        self.left = left
        self.right = right
        self.val = None
        self.star_idx = False
        if isinstance(left, NamespaceIndex) and left.star_idx:
            errors.error("Cannot get names from a `*` namespace index",
                         line=pos)

    def copy(self):
        out = NamespaceIndex(self._position, self.left.copy(), self.right.copy())
        out.star_idx = self.star_idx
        return out

    def reset(self):
        super().reset()
        self.left.reset()
        self.right.reset()
        self.val = None

    def fullfill_templates(self, func):
        self.left.fullfill_templates(func)

    def post_parse(self, func):
        self.left.post_parse(func)

    def pre_eval(self, func):
        if self.star_idx:
            errors.error("'*' index can only used in an import statement",
                         line=self.left.position)
        var = self.left.get_var(func)
        if isinstance(var, GenericSpecify):
            var = var.as_type_reference(func, True)

        if var is None:
            errors.error("Namespace does not exist",
                         line=self.left.position)
        self.val = var.get_namespace_name(func,
                                          self.right.var_name,
                                          self.right.position)
        if isinstance(self.val, ExpressionNode):
            self.ret_type = self.val.ret_type
        else:
            self.ret_type = self.val

    def eval_impl(self, func):
        if isinstance(self.val, ExpressionNode):
            return self.val.eval(func)

        errors.error("Namespace cannot be evaluated like an expression",
                     line=self.left.position)

    def get_var(self, func):
        self.pre_eval(func)
        return self.val

    def get_lifetime(self, func):
        return self.get_var(func).get_lifetime(func)

    def as_type_reference(self, func, allow_generics=False):
        self.pre_eval(func)
        if isinstance(self.val, Ast_Types.Type):
            return self.val
        print(self.val)
        errors.error("Not a type", line=self.position)

    def as_file_path(self):
        '''for imports'''
        if isinstance(self.left, NamespaceIndex):
            left = self.left.as_file_path()
        else:
            left = self.left.var_name

        if self.star_idx:
            right = ""
        else:
            right = f"/{self.right.var_name}.bcl"

        file = f"{left}{right}"
        # folder = f"{left}/{right}/init.bcl"

        return file


    def get_position(self) -> SrcPosition:
        if self.star_idx:
            return self.left.position
        return self.merge_pos((self.left.position, self.right.position))

    def get_function(self, func):
        errors.error("FUCK", line=self.position)
