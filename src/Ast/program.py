# '''This module contains global state
# and other functions related to the compilation
# of the program as a whole. A module is used instead of a class
# because there is only ever one program being compiled
# '''

# from collections import deque

# from llvmlite import binding

# from rply.errors import LexingError

# import errors
# import linker
# from Ast.functions import standardfunctions
# from Ast.module import Module
# from Ast.nodes.commontypes import SrcPosition

# modules: list[Module] = list([])


# def add_module_queue(module):
#     global modules
#     modules.append(module)


# def parse_modules():
#     count = 0
#     try:
#         while len(modules) > count:
#             current = modules[count]
#             standardfunctions.declare_globals(modules[count].module)
#             standardfunctions.declare_all(modules[count].module)
#             current.parse()
#             count += 1
#     except LexingError as e:
#         error_pos = e.source_pos
#         pos = SrcPosition(error_pos.lineno, error_pos.colno, 0, current.location)
#         errors.error("A Lexing Error has occured. Invalid Syntax",
#                      line=pos, full_line=True)


# def eval_modules():
#     for current in modules:
#         current.pre_eval()

#     for current in modules:
#         current.eval()


# def create_binary(args, loc):
#     object_files = []
#     # llir = str(modules[0].module)
#     main_mod = modules[0].save_ir(modules[0].location, args=args, create_object=True)
#     for current in modules[1:]:
#         mod = current.save_ir(current.location, args=args, create_object=True)
#         object_files.append(f"{current.location}.o")
#         main_mod.link_in(mod)

#     target = modules[0].target.create_target_machine(force_elf=True, codemodel="default")

#     with open(f"{loc}.o", 'wb') as output_file:
#         output_file.write(target.emit_object(mod))

#     # current.save_ir(main_mod.location, args=args)
#     object_files.append(f"{modules[0].location}.o")

#     if args["--emit-binary"]:
#         extra_args = [f"-l{x}" for x in args["--libs"]]
#         linker.link_all(loc, object_files, extra_args)
