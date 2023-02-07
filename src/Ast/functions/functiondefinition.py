class FunctionDef(ASTNode):
    '''Defines a function in the IR'''
    __slots__ = ('builder', 'block', 'function_ir', 'args', 'args_ir', 'module','is_ret_set',
                'args_types', 'ret_type', "has_return", "inside_loop", "func_name", "variables", "consts",
                "ir_entry")
    # type = NodeTypes.STATEMENT
    # name = "funcDef"

    def __init__(self, pos: SrcPosition, name: str, args: ParenthBlock, block: Block, module: Module):
        self._position   = pos
        self.func_name   = name
        self.ret_type: Ast_Types.Type = Ast_Types.Void() # Can also be a TypeRef. In which case, it should be evaled

        self.builder     = None   # llvmlite.ir.IRBuilder object once created
        self.block       = block  # body of the function Ast.Block
        self.module      = module # Module the object is contained in
        self.is_ret_set  = False  # is the return value set?
        self.has_return  = False  # Not to be confused with "is_ret_set", this is used for ensuring that a `return` always accessible
        self.inside_loop = None   # Whether or not the IRBuilder is currently inside a loop block, set to the loop node
        self.ir_entry    = None   # Entry section of the function. Used when declaring "invisible" variables
        self.variables: list[tuple] = []
        self.consts: list[tuple] = []

        self._validate_args(args) # validate arguments

        # construct args lists
        self.args: dict[str, ExpressionNode] = dict()
        self.args_ir: tuple[ir.Type, ...] = () # list of all the args' ir types
        self.args_types: tuple[Ast_Types.Type, ...] = () # list of all the args' Ast_Types.Type return types
        self._construct_args(args)
        
    
    def _construct_args(self, args: ParenthBlock):
        '''Construct the lists of args required when building this function'''
        args_ir    = []
        args_types = []
        for arg in args:
            self.args[arg.key.var_name] = [None, arg.value.as_type_reference(), True] #type: ignore
            if arg.get_type().pass_as_ptr:
                args_ir.append(arg.get_type().ir_type.as_pointer())
            else:
                args_ir.append(arg.get_type().ir_type)
            args_types.append(arg.get_type())
        
        self.args_ir = tuple(args_ir)
        self.args_types = tuple(args_types)


    def _validate_args(self, args: ParenthBlock):
        '''Validate that all args are syntactically valid'''
        if not args.is_key_value_pairs():
            errors.error(f"Function {self.func_name}'s argument tuple consists of non KV_pairs", line = self.position)

    def _validate_return(self):
        ret_line = (-1,-1,-1)
        if self.is_ret_set:
            # self.ret_type.eval(self)
            ret_line = self.ret_type.position
            self.ret_type = self.ret_type.as_type_reference()
        if (not self.ret_type.returnable) and self.block is not None :
            errors.error(f"Function {self.func_name} cannot return a reference to a local variable or value.", line = ret_line)

    def _mangle_name(self, name) -> str:
        '''add an ID to the end of a name if the function has a body and is NOT named "main"'''
        return self.module.get_unique_name(name)

    def _append_args(self):
        '''append all args as variables usable inside the function body'''
        args = self.function_ir.args
        for c,x in enumerate(self.args.keys()):
            self.block.variables[x].ptr = args[c]
            self.variables.append((self.block.variables[x], x))
    
    def pre_eval(self):
        global functions

        self._validate_return()
        fnty = ir.FunctionType((self.ret_type).ir_type, self.args_ir, False)

        if self.func_name not in functions:
            # Ast_Types.Type_Function.Function(self.func_name, self.module)
            functions[self.func_name] = dict()


        self.function_ir = ir.Function(self.module.module, fnty, name=self._mangle_name(self.func_name))
        functions[self.func_name][self.args_types] = _Function(_Function.BEHAVIOR_DEFINED,
                                                          self.func_name, self.function_ir,
                                                          self.ret_type, self.args_types) # TODO: REMOVE
        
        # Early return if the function has no body.
        if self.block is None:
            return

        block = self.function_ir.append_basic_block("entry")
        self.builder = ir.IRBuilder(block)
        self.ir_entry = block
        self._append_args()

    def create_const_var(self, typ):
        current_block = self.builder.block
        self.builder.position_at_start(self.ir_entry)
        ptr = self.builder.alloca(typ.ir_type, name=self._mangle_name("CONST"))
        self.builder.position_at_end(current_block)
        return ptr

    def alloc_stack(self):
        for x in self.variables:
            if x[0].is_constant:
                if x[0].type.pass_as_ptr:
                    val = self.builder.load(x[0].ptr)
                else:
                    val = x[0].ptr
                if not x[0].type.no_load:
                    ptr = self.builder.alloca(x[0].type.ir_type)
                    self.builder.store(val, ptr)
                    x[0].ptr = ptr
                x[0].is_constant = False
                continue
            else:
                x[0].define(self, x[1])

    def eval(self):
        if self.block is None:
            return
        self.function_ir.attributes.add("nounwind")
        self.block.pre_eval(self)
        self.alloc_stack()

        args = self.function_ir.args  # TODO: REMOVE UNUSED
        
        self.block.eval(self)
        
        if self.ret_type.is_void():
            self.builder.ret_void()
        elif not self.has_return:
            errors.error(f"Function '{self.func_name}' has no guaranteed return! Ensure that at least 1 return statement is reachable!")