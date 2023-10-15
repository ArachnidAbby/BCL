import platform
import sys

from cx_Freeze import Executable, setup

build_exe_options = {
    "excludes": ["tkinter", "unittest", "numpy", "mypy", "http", "email", "sphinx"],
    "bin_includes": [],
    "include_files": [("src/libbcl/", "lib/libbcl/"), ("docs/build/html", "docs/")]
}

if platform.system() == 'Windows':
    build_exe_options["bin_includes"].append("env/lib/llvmlite/binding/libllvmlite.dll")
else:
    build_exe_options["bin_includes"].append("env/lib/llvmlite/binding/libllvmlite.so")

sys.path.append("src/")

setup(
    name="BCL",
    version="0.7",
    description="The BCL language's compiler",
    options={"build_exe": build_exe_options},
    executables=[Executable("src/main.py", icon="docs/source/_static/experimental_BCL_LOGO.ico")],

)
