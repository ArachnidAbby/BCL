
from llvmlite import binding
from llvmlite.ir import Module


#todo: defer this functionality to a simple function, not a class
class CodeGen():
    __slots__ = ("module")

    def __init__(self):
        binding.initialize()
        binding.initialize_native_target()
        binding.initialize_native_asmprinter()
        self._config_llvm()

    def _config_llvm(self):
        self.module = Module(name=__file__)
        self.module.triple = binding.get_default_triple()

    def save_ir(self, filename):
        with open(filename, 'wb') as output_file:
            output_file.write(binding.ModuleRef(str(self.module), self.module.context).as_bitcode())

    def shutdown(self):
        binding.shutdown()
