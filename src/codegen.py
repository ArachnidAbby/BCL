
from llvmlite import binding  # type: ignore


def initialize_llvm():
    binding.initialize()
    binding.initialize_native_target()
    binding.initialize_native_asmprinter()


def shutdown_llvm():
    binding.shutdown()
