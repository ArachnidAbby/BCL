from Ast.arrays.index import VariableIndexRef
from Ast.Ast_Types import Void
from Ast.nodes import ASTNode, ExpressionNode
from Ast.nodes.commontypes import SrcPosition
from Ast.variables.reference import VariableRef
from Ast.variables.varobject import VariableObj
from errors import error


class VariableAssign(ASTNode):
    '''Handles Variable Assignment and Variable Instantiation.'''
    __slots__ = ('value', 'block', 'is_declaration', 'var_name',
                 'explicit_typ', 'typ')

    def __init__(self, pos: SrcPosition, ptr: ExpressionNode, value,
                 block, typ=Void()):
        self._position = pos
        if not ptr.assignable:
            error("Entity is not assignable.", line=ptr.position)
        self.var_name = ptr
        self.is_declaration = False
        self.value = value
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

        if name not in self.block.variables.keys():
            self.typ = self.typ.as_type_reference()
            self.block.variables[name] = VariableObj(None, self.typ,
                                                     False)
            self.is_declaration = True

        if self.block.get_variable(name).type.is_void():
            self.block.variables[name].type = self.value.ret_type

        var_search_tuple = (self.block.get_variable(name),
                            name)
        if var_search_tuple not in func.variables:
            variable = self.block.get_variable(name)
            func.variables.append((variable, name))

    def pre_eval(self, func):
        self.value.pre_eval(func)
        if self.block is None:
            return

        self.create_new_var(func)

        if not self.is_declaration and self.explicit_typ:
            error("Cannot declare the type of a variable after initial" +
                  " declaration", line=self.position)

        self.var_name.pre_eval(func)

    def set_not_constant(self, func):
        '''set a variable object's is_constant attribute to False'''
        if not isinstance(self.var_name, VariableRef):
            return

        name = self.var_name.var_name
        if self.block.validate_variable(name):
            self.block.variables[name].is_constant = False

    def eval(self, func):
        self.value.pre_eval(func)
        ptr = self.var_name.get_ptr(func)
        self.set_not_constant(func)
        typ = self.var_name.ret_type
        typ.assign(func, ptr, self.value, typ)
