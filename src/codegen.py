
from llvmlite import binding
from llvmlite.ir import Module


class CodeGen():
    __slots__ = ('module')

    def __init__(self):
        binding.initialize()
        binding.initialize_native_target()
        binding.initialize_native_asmprinter()
        self._config_llvm()

    def _config_llvm(self):
        self.module = Module(name=__file__)
        self.module.triple = binding.get_default_triple()

    def save_ir(self, filename):
        with open(filename, 'w') as output_file:
            output_file.write(str(self.module))
