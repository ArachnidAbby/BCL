# from lexer import Lexer
# from parser import Parser
# from codegen import CodeGen

# fname = "src/input.bcl"
# with open(fname) as f:
#     text_input = f.read()

# lexer = Lexer()
# tokens = lexer.tokenize(text_input)

# codegen = CodeGen()

# module = codegen.module
# builder = codegen.builder
# printf = codegen.printf

# # for x in tokens:
# #     print(x)

# pg = Parser(module, builder, printf)
# parsed = pg.parse(tokens)
# for x in parsed:
#     print(x)
# #parsed.eval()
# # parser = pg.get_parser()
# # parser.parse(tokens).eval()
# print(module)
# codegen.create_ir()
# codegen.save_ir("src/output.ll")

from lexer import Lexer
from parser import Parser
from codegen import CodeGen

fname = "src/testing/input.bcl"
with open(fname) as f:
    text_input = f.read()

lexer = Lexer().get_lexer()
tokens = lexer.lex(text_input)

codegen = CodeGen()

module = codegen.module
builder = codegen.builder
printf = codegen.printf

pg = Parser(module, builder, printf)
pg.parse()
parser = pg.get_parser()
x = parser.parse(tokens)
x.eval()

codegen.create_ir()
codegen.save_ir("src/testing/output.ll")