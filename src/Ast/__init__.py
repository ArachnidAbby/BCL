
from typing import List, Tuple
from llvmlite import ir
from .Nodes import *
from .Variable import *
from .Math import *
from .Function import *
from . import Containers, Standard_Functions, Types

# class Program:
#     def __init__(self,builder,module):
#         self.stuff = []
#         self.builder = builder
#         self.module = module
#         self.value=""
        
#         #printing integers using a bitcast requires a string constant.

#         fmt = "%i \n\0"
#         c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
#                             bytearray(fmt.encode("utf8")))
#         self.global_fmt_int_n = ir.GlobalVariable(self.module, c_fmt.type, name="fstr_int_n")
#         self.global_fmt_int_n.linkage = 'internal'
#         self.global_fmt_int_n.global_constant = True
#         self.global_fmt_int_n.initializer = c_fmt
        
#         voidptr_ty = ir.IntType(8).as_pointer()
#         self.fmt_int_n = self.builder.bitcast(self.global_fmt_int_n, voidptr_ty)

#         fmt = "%i \0"
#         c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
#                             bytearray(fmt.encode("utf8")))
#         self.global_fmt_int = ir.GlobalVariable(self.module, c_fmt.type, name="fstr_int")
#         self.global_fmt_int.linkage = 'internal'
#         self.global_fmt_int.global_constant = True
#         self.global_fmt_int.initializer = c_fmt

#         #printing integers using a bitcast requires a string constant.

#         fmt = "%s \n\0"
#         c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
#                             bytearray(fmt.encode("utf8")))
#         self.global_fmt_string_n = ir.GlobalVariable(self.module, c_fmt.type, name="fstr_string_n")
#         self.global_fmt_string_n.linkage = 'internal'
#         self.global_fmt_string_n.global_constant = True
#         self.global_fmt_string_n.initializer = c_fmt

#         voidptr_ty = ir.IntType(8).as_pointer()
#         self.fmt_string_n = self.builder.bitcast(self.global_fmt_string_n, voidptr_ty)

#         fmt = "%s \0"
#         c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
#                             bytearray(fmt.encode("utf8")))
#         self.global_fmnt_string = ir.GlobalVariable(self.module, c_fmt.type, name="fstr_string")
#         self.global_fmnt_string.linkage = 'internal'
#         self.global_fmnt_string.global_constant = True
#         self.global_fmnt_string.initializer = c_fmt
    
#     def eval(self):
#         output = []
#         for x in self.stuff:
#             output.append(x.eval())
#         return output
    
#     def append(self,thing):
#         self.stuff.append(thing)

# class Parenth():
#     def __init__(self,*args):
#         self.stuff = []
    
#     def eval(self):
#         output = []
#         for x in self.stuff:
#             #print(x)
#             output.append(x.eval())
#         return output
    
#     def __len__(self):
#         return len(self.stuff)
    
#     def append(self,thing):
#         self.stuff.append(thing)

# class Block():
#     def __init__(self,*args):
#         self.stuff = []
    
#     def eval(self):
#         output = []
#         for x in self.stuff:
#             #print(x)
#             output.append(x.eval())
#         return output
    
#     def __len__(self):
#         return len(self.stuff)
    
#     def append(self,thing):
#         self.stuff.append(thing)
#     def __init__(self,builder,module):
#         self.stuff = []
#         self.builder = builder
#         self.module = module
#         self.value=""
        
#         #printing integers using a bitcast requires a string constant.

#         fmt = "%i \n\0"
#         c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
#                             bytearray(fmt.encode("utf8")))
#         self.global_fmt_int_n = ir.GlobalVariable(self.module, c_fmt.type, name="fstr_int_n")
#         self.global_fmt_int_n.linkage = 'internal'
#         self.global_fmt_int_n.global_constant = True
#         self.global_fmt_int_n.initializer = c_fmt
        
#         voidptr_ty = ir.IntType(8).as_pointer()
#         self.fmt_int_n = self.builder.bitcast(self.global_fmt_int_n, voidptr_ty)

#         fmt = "%i \0"
#         c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
#                             bytearray(fmt.encode("utf8")))
#         self.global_fmt_int = ir.GlobalVariable(self.module, c_fmt.type, name="fstr_int")
#         self.global_fmt_int.linkage = 'internal'
#         self.global_fmt_int.global_constant = True
#         self.global_fmt_int.initializer = c_fmt

#         #printing integers using a bitcast requires a string constant.

#         fmt = "%s \n\0"
#         c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
#                             bytearray(fmt.encode("utf8")))
#         self.global_fmt_string_n = ir.GlobalVariable(self.module, c_fmt.type, name="fstr_string_n")
#         self.global_fmt_string_n.linkage = 'internal'
#         self.global_fmt_string_n.global_constant = True
#         self.global_fmt_string_n.initializer = c_fmt

#         voidptr_ty = ir.IntType(8).as_pointer()
#         self.fmt_string_n = self.builder.bitcast(self.global_fmt_string_n, voidptr_ty)

#         fmt = "%s \0"
#         c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
#                             bytearray(fmt.encode("utf8")))
#         self.global_fmnt_string = ir.GlobalVariable(self.module, c_fmt.type, name="fstr_string")
#         self.global_fmnt_string.linkage = 'internal'
#         self.global_fmnt_string.global_constant = True
#         self.global_fmnt_string.initializer = c_fmt
    
#     def eval(self):
#         output = []
#         for x in self.stuff:
#             output.append(x.eval())
#         return output
    
#     def append(self,thing):
#         self.stuff.append(thing)

