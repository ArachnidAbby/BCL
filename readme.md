![BCL logo](docs/source/_static/experimental_BCL_LOGO.png)

![Project Status](https://img.shields.io/badge/Project%20Status-In%20Development-orange?style=for-the-badge) ![GitHub last commit](https://img.shields.io/github/last-commit/spidertyler2005/BCL?style=for-the-badge) ![Discord](https://img.shields.io/discord/875155614202994761?style=for-the-badge)

# What is BCL?

BCL (Ben's Compiled Language) is a compiled programming language that is inspired by python and other languages.

# Installing via source

To do this you will need:
- LLVM 14 (or LLVM11 if using alternative fork)
- Conda
- Python 3.11+
- SetupTools (`pip install setuptools`)

### Step 1

Clone the git repo

### Step 2

run these commands


```sh
# libs required to compile llvmlite from source/custom fork
## linux gcc stuff, I couldn't get it to compile without this
conda install -c conda-forge libstdcxx-ng=12
## llvm14 install (change 14 to 11 if needed)
conda install -y -q -c numba/label/dev llvmdev="14.*" libxml2
## llvm uses cmake
conda install cmake

# Installing custom llvmlite fork that has lld for linking (LLVM14)
pip install git+https://github.com/Hassium-Software/llvmlite-lld.git
# Alternatively, if this doesn't work install (LLVM11)
pip install git+https://github.com/spidertyler2005/llvmlite.git

# Installing repo
pip install .
```

### Step 3

run `bcl <subcommand> <args>` to use BCL!

### How to uninstall

run `pip uninstall Bens_Compiled_Language`

# Example code

```
//  fizzbuzz program
// ===================

import stdlib; // will later be an auto-import

define main() {
    for i in 0..100 {
        // printf is in the language, could be used here too!
        print(i);
        print(' ');
        if is_multiple(i, 3) {
            print("fizz");
        }
        if is_multiple(i, 5) {
            print("buzz");
        }
        println();
    }
}

define is_multiple(value: i32, divider: i32) -> bool {
    return (value % divider) == 0;
}
```

# State of the language

The language is *not* fit for production use. It is missing a very large number of features. Although, it is turing-complete.

## Features

- [x] codeblocks
- [x] functions
- [x] function returns
- [x] function arguments
- [x] variable declaration and assignment
- [x] most Operators (now with 100% more bitwise ops)
- [x] boolean operators
- [x] if and else statements
- [x] while loops
- [x] floats
- [x] variable type declaration
- [x] variable assignment-operators (`+=`, `-=`, etc)
- [x] Arrays
- [x] for-loops (only with range literals rignt now)
- [x] references
- [ ] `const`ants
- [x] structs
- [x] struct functions
- [x] struct methods
- [x] struct operator overloading
- [ ] struct generic typing
- [ ] protocol types
- [x] generator functions/iterators
- [x] `import` statement with the ability to import modules/packages (WIP, needs namespaces)
- [x] compile a folder or file instead of hardcoded test string.
- [ ] heap allocation with garbage collection
- [ ] `del` or `free` statement (only work when GC is off, otherwise they decrease the ref count by 1)
- [ ] in-line assembly functionality.
- [ ] make sys-calls
- [x] ~~some access to llvm function directly. (notice: more can, and will, be added)~~ disabled temporarily
- [ ] access to cpu registers.
- [x] standard math library (VERY VERY WIP)
- [x] string (literal)
- [ ] strings (mutable)
- [ ] vectors
- [x] stdio library (VERY WIP)
- [ ] run-time errors (Error type for errors as values.)
- [ ] Option type
- [x] namespaces
- [x] enums


# VSCode highlighting

There is a folder called `syntax_highlighting`, inside there is a vsix file which you can right click to install. Just note that it's a bit of a work in progress.

# Documentation

Sphinx documentation can be found in the `docs` folder. Note that these docs are not up-to-date yet.