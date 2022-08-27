# What is BCL?

BCL (Ben's Compiled Language) is a compiled programming language that is inspired by python and other languages.

# State of the language

The language is *not* fit for production use. It is missing a very large number of features.

## Features

- [x] codeblocks
- [x] functions
- [x] function returns
- [x] function arguments
- [x] variable declaration and assignment
- [x] most Operators (excluding `**` for now)
- [x] boolean operators
- [x] if and else statements
- [x] while loops
- [ ] floats
- [ ] variable type declaration
- [ ] variable assignment-operators (`+=`, `-=`, etc)
- [ ] Lists
- [ ] for-loops
- [ ] points/references
- [ ] `const`ants
- [ ] structs
- [ ] struct functions
- [ ] struct operator overloading
- [ ] `import` statement with the ability to import modules/packages
- [ ] compile a folder or file instead of hardcoded test string.
- [ ] heap allocation with garbage collection
- [ ] `del` or `free` statement (only work when GC is off)
- [ ] in-line assembly functionality.
- [ ] make sys-calls
- [ ] some access to llvm function directly.
- [ ] access to cpu registers.
- [ ] standard math library
- [ ] strings
- [ ] vectors
- [ ] stdio library
- [ ] run-time errors


# VSCode highlighting

There is a folder called `syntax_highlighting`, inside there is a vsix file which you can right click to install. Just note that it's a bit of a work in progress.

# Documentation

Sphinx documentation can be found in the `docs` folder. Note that these docs are not up-to-date yet.