from Ast.Ast_Types import Void
from Ast.nodes import ASTNode, ExpressionNode
from Ast.nodes.commontypes import SrcPosition
from Ast.variables.reference import VariableRef
from Ast.variables.varobject import VariableObj
from errors import error


class VariableAssign(ASTNode):
    '''Handles Variable Assignment and Variable Instantiation.'''
    __slots__ = ('value', 'block', 'is_declaration', 'var_name',
                 'explicit_typ', 'typ', 'evaled_value')

    def __init__(self, pos: SrcPosition, ptr: ExpressionNode, value,
                 block, typ=Void()):
        self._position = pos
        if not ptr.assignable:
            error("Entity is not assignable.", line=ptr.position)
        self.var_name = ptr
        self.is_declaration = False
        self.value = value
        self.evaled_value = None
        self.block = block
        self.explicit_typ = typ != Void  # TODO: GROSS AS FUCK
        self.typ = typ

    def create_new_var(self, func):
        '''create new variable if it does not exist.
        This requires the self.var_name attribute to be a
        VariableRef node.
        '''
        if not isinstance(self.var_name, VariableRef):
            return

        name = self.var_name.var_name

        if not self.block.get_variable(name):
            self.typ = self.typ.as_type_reference(func)
            self.block.variables[name] = VariableObj(None, self.typ,
                                                     False)
            self.is_declaration = True

        if self.block.get_variable(name).type.is_void():
            # if self.value.ret_type.name == 'ref':  #! TEMP
            #     self.block.get_variable(name).type = self.value.ret_type.typ
            # else:
            self.block.get_variable(name).type = self.value.ret_type.get_assign_type(func, self.value)

        var_search_tuple = (self.block.get_variable(name),
                            name)
        if var_search_tuple not in func.variables and name not in func.args:
            variable = self.block.get_variable(name)
            func.variables.append((variable, name))
            if func.yields:
                func.yield_gen_type.add_members(func.yield_consts,
                                                [x[0].type for x in func.variables])

    def pre_eval(self, func):
        self.value.pre_eval(func)
        if self.block is None:
            return

        self.create_new_var(func)
        if not self.is_declaration and self.explicit_typ:
            error("Cannot declare the type of a variable after initial" +
                  " declaration", line=self.position)

        self.var_name.pre_eval(func)
        if not self.var_name.assignable:
            error("Cannot assign value to non-assignable variable/member",
                  line=self.var_name.position)

        # if self.typ.needs_dispose:
        #     func.register_dispose(self)

    def set_not_constant(self, func):
        '''set a variable object's is_constant attribute to False'''
        if not isinstance(self.var_name, VariableRef):
            return

        name = self.var_name.var_name
        if self.block.validate_variable(name):
            self.block.get_variable(name).is_constant = False

    def eval_impl(self, func):
        self.value.pre_eval(func)
        self.value.overwrite_eval = True
        ptr = self.var_name
        self.set_not_constant(func)
        typ = self.var_name.ret_type
        if not self.is_declaration and typ.needs_dispose:
            typ.dispose(func, ptr)
        elif typ.needs_dispose:
            func.register_dispose(ptr)
        typ.assign(func, ptr, self.value, typ,
                   first_assignment=self.is_declaration)

    def repr_as_tree(self) -> str:
        return self.create_tree("Variable Assignment",
                                value=self.value,
                                var=self.var_name)
