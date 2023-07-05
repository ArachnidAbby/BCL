from Ast.variables.reference import VariableRef
from Ast.literals import Literal
from Ast.Ast_Types.Type_Enums import EnumType
from Ast.Ast_Types.Type_I32 import Integer_32
from Ast.nodes.astnode import ASTNode
from Ast.nodes.keyvaluepair import KeyValuePair
import errors


class Definition(ASTNode):
    __slots__ = ('enum_name', 'members', 'enum_type', 'module')

    def __init__(self, pos, name, members, module):
        super().__init__(pos)

        self.members = members
        if not isinstance(name, VariableRef):
            errors.error("Enum name must be a variable-like name",
                         line=name.position)
        self.enum_name = name.var_name
        self.module = module

        members_list = []

        for member in members[0].children:
            if isinstance(member, KeyValuePair):
                members_list.append((member.key.var_name, member.key.position))
            elif isinstance(member, VariableRef):
                members_list.append((member.var_name, member.position))
            else:
                errors.error("Enum variant names must be actual names.",
                             line=pos)

        self.enum_type = EnumType(name, module.mod_name, pos, members_list)
        module.create_type(self.enum_name, self.enum_type)
        module.add_enum_to_schedule(self)

    def scheduled(self, parent):
        members_list = []

        for member in self.members[0].children:
            if isinstance(member, KeyValuePair):
                if not member.value.isconstant \
                        and not isinstance(member.value.ret_type, Integer_32):
                    errors.error("Enum variants must be integers",
                                 line=member.value.position)
                members_list.append((member.key.var_name, member.value,
                                     member.position))
            elif isinstance(member, VariableRef):
                members_list.append((member.var_name, None, member.position))
        self.enum_type.create_values(self, members_list, self.position)
