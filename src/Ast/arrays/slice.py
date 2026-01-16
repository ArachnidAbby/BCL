
from Ast.nodes import ExpressionNode
from Ast.nodes.commontypes import SrcPosition
from Ast.variables.reference import VariableRef


class SliceOperator(ExpressionNode):
    '''The slice Operation on an array'''
    __slots__ = ('start', 'end', 'step', 'varref')

    # TODO: MAKE SLICE ASSIGNMENT REAL AND BASED
    # assignable = True

    def __init__(self, pos: SrcPosition, varref: VariableRef,
                 start: ExpressionNode | None, end: ExpressionNode | None,
                 step: ExpressionNode | None):
        super().__init__(pos)
        self.varref = varref
        self.start = start
        self.end = end
        self.step = step

    def copy(self):
        # Gross, but I'm too lazy to fix it.
        start = self.start.copy() if self.start is not None else None
        end = self.end.copy() if self.end is not None else None
        step = self.step.copy() if self.step is not None else None

        return SliceOperator(self._position, self.varref.copy(),
                             start, end, step)

    def fullfill_templates(self, func):
        self.varref.fullfill_templates(func)
        if self.start is not None:
            self.start.fullfill_templates(func)
        if self.end is not None:
            self.end.fullfill_templates(func)
        if self.step is not None:
            self.step.fullfill_templates(func)

    def pre_eval(self, func):
        self.varref.pre_eval(func)

        if self.start is not None:
            self.start.pre_eval(func)
        if self.end is not None:
            self.end.pre_eval(func)
        if self.step is not None:
            self.step.pre_eval(func)

        var_ref_type = self.varref.ret_type
        self.ret_type = var_ref_type.get_slice_return(func, self.varref,
                                                      self.start, self.end,
                                                      self.step)

    def get_var(self, func):
        return self.varref.get_var(func)

    def eval_impl(self, func):
        var_ref_type = self.varref.ret_type
        return var_ref_type.make_slice(func, self.varref, self.start,
                                       self.end, self.step)

    def get_lifetime(self, func):
        return self.varref.get_lifetime(func)

    def __repr__(self) -> str:
        return f"<slice of `{self.varref}`>"

    def repr_as_tree(self) -> str:
        return self.create_tree("Slice Operator",
                                item=self.varref,
                                start=self.start,
                                end=self.end,
                                step=self.step,
                                return_type=self.ret_type)
