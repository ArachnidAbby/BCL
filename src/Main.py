import time

start = time.perf_counter()

from lexer import Lexer
import parser,_AST
from codegen import CodeGen
import json

fname = "src/testing/input.bcl"
with open(fname) as f:
    text_input = f.read()

with open('src/languageOptions/Colors.json') as f:
    colors = json.loads(f.read())

print(f'{colors["ok"]}/-------------------------------------------------{colors["reset"]}')
print(f'{colors["ok"]}| imports finished in {time.perf_counter() - start} seconds{colors["reset"]}')
start=time.perf_counter()

lexer = Lexer().get_lexer()
tokens = lexer.lex(text_input)
output = []
for x in tokens:
    output.append({"name":x.name,"value":x.value,"source_pos":x.source_pos})

print(f'{colors["info-warn"]}|',len(output), f'tokens{colors["reset"]}')
print(f'{colors["ok"]}| lexing finished in {time.perf_counter() - start} seconds{colors["reset"]}')
start=time.perf_counter()
#print(output)

codegen = CodeGen()

module = codegen.module
builder = codegen.builder
printf = codegen.printf

# try:
pg = parser.parser(output, builder,module,printf)
# x = pg.parse()
parsed = pg.parse()
g = _AST.VariableDeclaration("test", pg.program, pg.printf,-1)
parsed.append({"value":g})
for x in parsed:
    x["value"].eval()
print(f'{colors["ok"]}| parsing finished in {time.perf_counter() - start} seconds{colors["reset"]}')
start=time.perf_counter()
# except Exception as e:
#     print(e)

codegen.create_ir()
codegen.save_ir("src/testing/output.ll")

end = time.perf_counter()
print(f'{colors["ok"]}| compiled in {end - start} seconds{colors["reset"]}')
print(f'{colors["ok"]}\\-------------------------------------------------{colors["reset"]}')
# p = parser.parser(output,builder,module)
# program = "42"
# print(output)
# print()
# print(p.parse())