# Features required for bootstrapping

These are all features that I need to bootstrap effectively. It is technically possible to do it with less,
but I don't want to waste my time.

- [ ] Type unions
- [ ] constants
- [x] Properly working generics for structs
- [x] Vector and Box types
- [ ] Strings
- [ ] Slice type
- [ ] A binding of LLVM14 or higher
- [ ] A working regex library
- [X] Optional::<T> (generics need fixing)
- [X] Visibility modifiers
- [ ] File handling


# Features I would prefer to have

These features aren't required, but would make life significantly easier

- [ ] Protocol types
- [ ] Function pointers
- [ ] lifetimes to be able to return usually unreturnable types
- [ ] Generic functions
- [ ] import individual items from a namespace

# Completely optional

Would be nice to have, but not really necessary and wouldn't affect my ability to bootstrap the language.

- [ ] Several compile-time modifiers for functions: aliases, OS requirement for function compilation, dll/so export, etc.
- [ ] Meta programming functions
    - [x] Getting size of types (::SIZEOF). This specifically is not Optional
    - [ ] (to be determined)
- [ ] Proper name-mangling (completely unnecessary RIGHT NOW)
- [ ] namespace declaration