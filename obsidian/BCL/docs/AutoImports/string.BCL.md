# What is `string.bcl`?

`string.bcl` Implements a full string datatype with formatting, mutability, and other basic string features.

# Built-in Functions

- ~add(string other)
- ~mul(int number)
- format(Type[] ....stuff) -> `this`
- replace(string find, string replace) -> `this`
- find(string find) -> int[]
- findRegex(string regexFind) -> int[]
-  to_charArray() -> char[]

# Why use `string` over `char[]`

Char Array are immutable which can be problematic in some cases. For example, String formating.