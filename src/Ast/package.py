import os
from pathlib import Path
from typing import Optional

import errors
from Ast import Ast_Types
from Ast.nodes.astnode import ASTNode
from Ast.nodes.commontypes import SrcPosition
from lexer import Lexer


def _create_module(cmd_args, name: str, file: Path):
    from Ast.module import Module
    with open(file, 'r') as f:
        src_str = f.read()
        tokens = Lexer().get_lexer().lex(src_str)
    return Module(SrcPosition.invalid(), name, file, tokens, cmd_args)


def get_all_packages(cwd: Path, cmd_args: dict, starting_pkg=None) -> "Package":
    if starting_pkg is None:
        starting_pkg = Package(SrcPosition.invalid(), "", cwd)

    for item in os.listdir(cwd):
        full_path = cwd/item
        # item = item.strip()
        if os.path.isfile(full_path) and item.endswith(".bcl"):
            name = item[:-(len(".bcl"))]
            mod = _create_module(cmd_args, name, full_path)
            mod.package = starting_pkg
            starting_pkg.add_module(name, mod)
        elif not os.path.isfile(full_path):
            pkg = Package(SrcPosition.invalid(), item, full_path)
            get_all_packages(full_path, cmd_args, pkg)
            starting_pkg.add_package(item, pkg)

    return starting_pkg


class Package(ASTNode):
    __slots__ = ('location', 'pkg_name', 'parent_pkg', 'modules', 'packages')

    def __init__(self, pos: SrcPosition, pkg_name: str, location: Path):
        super().__init__(pos)
        self.location: Path = location
        self.pkg_name = pkg_name
        self.parent_pkg = None
        self.modules: dict[str, "Module"] = {}
        self.packages: dict[str, Package] = {}

    def get_namespace_name(self, func, name, pos, stack=None, override_star=False):
        from Ast.module import NamespaceInfo, alt_packages
        if name in self.packages.keys():
            return NamespaceInfo(self.packages[name], {})
        if name in self.modules.keys():
            return NamespaceInfo(self.modules[name], {})

        for pkg in alt_packages:
            out = pkg.get_namespace_name(func, name, pos, stack,
                                         override_star)
            if out is not None:
                return out

    def get_type_by_name(self, name, position, stack=None,
                         override_private=False) -> Optional[Ast_Types.Type]:
        pass

    def add_module(self, name: str, module):
        if name in self.modules.keys():
            errors.error("I'm not sure how you did this, but you have two modules of the same name???",
                         note=name + str(self.modules.keys()))
        self.modules[name] = module

    def add_package(self, name: str, package):
        if name in self.packages.keys():
            errors.error("I'm not sure how you did this, but you have two packages of the same name???")
        self.packages[name] = package
        package.parent_pkg = self

    def __str__(self) -> str:
        nlt = '\n\t' # new line + tab
        nl = '\n' # new line
        return f'''{self.pkg_name}/
\t\t{nlt.join([str(pkg) for pkg in self.packages.values() if len(pkg.modules) > 0]).replace(nl, nlt)}
\t\t{nlt.join([mod.mod_name for mod in self.modules.values()]).replace(nl, nlt)}'''.strip()

    def __repr__(self) -> str:
        return f"<Package: '{self.pkg_name}'>"

    def get_unique_name(self, name: str) -> str:
        if self.parent_pkg is None:
            return f"{self.pkg_name}.{name}"

        return self.parent_pkg.get_unique_name(f"{self.pkg_name}.{name}")

    def copy(self):
        return self

    def fullfill_templates(self, func):
        return super().fullfill_templates(func)