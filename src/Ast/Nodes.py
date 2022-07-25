from typing import List, Tuple
from llvmlite import ir

class AST_NODE:
    def __init__(self, position: Tuple[int,int], token: str, children: None|List = None, *args):
        self.type = ""
        self.name = ""
        self.position = position        # (line#, col#)
        self.token = token  # source code of this NODE.
        self.children = [] if children==None else children


        self.init(*args)
    
    def init(self):
        pass

    def eval(self):
        pass

    def show_er(self, source: List[str]) -> str:
        '''Show an error, 
            source: file's source seperated by lines.
        '''
        output = source[self.position[0]]+f'\n{" "*(self.position[1]-1)}'+f"{'^'*len(self.token)}"
        return output


class Block(AST_NODE):
    def init(self):
        self.name = "Block"
        self.type = "Block"

        self.variables = dict() # {name: ptr, ...}
        self.builder = None
    
    def append_child(self, child: AST_NODE):
        self.children.append(child)