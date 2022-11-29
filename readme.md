![BCL logo](docs/source/_static/experimental_BCL_LOGO.png)

![Project Status](https://img.shields.io/badge/Project%20Status-In%20Development-orange?style=for-the-badge) ![GitHub last commit](https://img.shields.io/github/last-commit/spidertyler2005/BCL?style=for-the-badge) ![Discord](https://img.shields.io/discord/875155614202994761?style=for-the-badge)

# What is BCL?

BCL (Ben's Compiled Language) is a compiled programming language that is inspired by python and other languages.

# Example code

```
//  fizzbuzz program
// ===================
// outputs
//   0: not fizz or buzz
//   1: fizz
//   2: buzz
///  3: fizzbuzz

define main() {
    i = 0;
    loop_amount = 200;
    while i < loop_amount {
        i = i+1;
        fizz = is_multiple(i, 3);
        buzz = is_multiple(i, 5)*2;
        println(fizz + buzz);
    }
}

define is_multiple(value: i32, divider: i32) -> bool {
    return (value % divider) == 0;
}
```

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
- [x] floats
- [ ] variable type declaration
- [ ] variable assignment-operators (`+=`, `-=`, etc)
- [x] Arrays
- [ ] for-loops
- [ ] pointers/references
- [ ] `const`ants
- [ ] structs
- [ ] struct functions
- [ ] struct operator overloading
- [ ] `import` statement with the ability to import modules/packages
- [x] compile a folder or file instead of hardcoded test string.
- [ ] heap allocation with garbage collection
- [ ] `del` or `free` statement (only work when GC is off)
- [ ] in-line assembly functionality.
- [ ] make sys-calls
- [x] some access to llvm function directly. (notice: more can, and will, be added)
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