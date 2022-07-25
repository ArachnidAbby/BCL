
from typing import List, Tuple

from llvmlite import ir

from . import Standard_Functions, Types
from .Function import *
from .Math import *
from .Nodes import *
from .Variable import *

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
