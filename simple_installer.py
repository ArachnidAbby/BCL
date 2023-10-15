'''
A "Quick install" option for BCL that sets everything up for you.
This could be completely broken if you use it, but it will try it's best.
Just because this script exists doesn't mean this setup process will work on every system.
It compiles llvm/llvmlite/lld which can be
a lot of trouble to get compiling (yay cmake).

DEPENDECIES:
- conda
- python >3.11
'''

import platform
import subprocess
import sys

USE_LLVM14_LINUX = "--llvm11" not in sys.argv


def section_break():
    print()
    print("-"*30)
    print()


print("NOTICE:")
print("""This quick install option for BCL runs the commands provided
in the readme used for installation. It does no more than that.
Correctness is NOT guaranteed. Please use caution!
""")

input("""Press ENTER to continue with installation.
Use ctrl + C or ctrl + Z (or whatever other shortcut your system uses) to close the installer""")

section_break()

print("Installing required conda packages (THIS MAY TAKE A WHILE)!")
# Install llvmlite dependencies
if platform.system() == "Linux":
    print("Installing libstdcxx-ng (required for llvm + lld compilation)")
    subprocess.run(["conda", "install", "-y", "-q", "-c", "conda-forge",
                    "libstdcxx-ng=12"])

if platform.system() == "Linux" and USE_LLVM14_LINUX:
    print("Installing LLVM14 (linux default, \"--llvm11\" to use llvm11)")
    subprocess.run(["conda", "install", "-y", "-q", "-c",
                    "numba/label/dev", "llvmdev=\"14.*\"", "libxml2"])
else:
    print("Installing LLVM11")
    subprocess.run(["conda", "install", "-y", "-q", "-c",
                    "numba/label/dev", "llvmdev=\"11.*\"", "libxml2"])

print("Installing CMAKE")
subprocess.run(["conda", "install", "cmake"])

# install llvmlite
if platform.system() == "Linux" and USE_LLVM14_LINUX:
    print("Installing llvmlite for LLVM14 (linux default, \"--llvm11\" to use llvm11)")
    subprocess.run(["pip", "install",
                    "git+https://github.com/Hassium-Software/llvmlite-lld.git"])  # llvm 14
else:
    print("Installing llvmlite for LLVM11")
    subprocess.run(["pip", "install",
                    "git+https://github.com/spidertyler2005/llvmlite.git"])  # llvm 11

section_break()
print("Installing BCL")

subprocess.run(["pip", "install", "."])

section_break()

print("Installation Finished!")
input("Press ENTER to exit.")
