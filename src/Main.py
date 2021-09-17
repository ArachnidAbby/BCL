import time

start = time.time()

from lexer import Lexer
from parser import Parser
from codegen import CodeGen
import json

fname = "src/testing/input.bcl"
with open(fname) as f:
    text_input = f.read()

with open('src/languageOptions/Colors.json') as f:
    colors = json.loads(f.read())

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

end = time.time()
print(f'{colors["green"]} compiled in {end - start} seconds{colors["reset"]}')