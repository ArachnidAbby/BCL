from llvmlite import ir
import codecs

class String_utf8():
    ID = 0
    def __init__(self, builder, module, value):
        self.builder = builder
        self.module = module
        self.value = value
        self.type = "string"

    def eval(self):
        fmt = self.value[1:-1]
        fmt = codecs.escape_decode(fmt.encode())[0].decode()
        print(codecs.escape_decode(fmt.encode()))
        c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                            bytearray(fmt.encode("utf8")))
        self.global_fmt_int_n = ir.GlobalVariable(self.module, c_fmt.type, name="StringConst_"+str(String_utf8.ID))
        self.global_fmt_int_n.linkage = 'internal'
        self.global_fmt_int_n.global_constant = True
        self.global_fmt_int_n.initializer = c_fmt
        
        voidptr_ty = ir.IntType(8).as_pointer()
        output = self.builder.bitcast(self.global_fmt_int_n, voidptr_ty)
        String_utf8.ID +=1
        return output