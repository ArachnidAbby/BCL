# BCL standard library.

This folder is a fallback for if a module isn't found in other search paths.

This means it will have all the provided modules and packages available for users, except for when users shadow the names.



# Adding to the standard library

There are a few things to keep in mind.

Keep in mind a lot of these are not hard rules and exceptions can be made.

## Don't be too opinionated

Features shouldn't be incredibly opinionated about how the user should write their code.

We want to support as many paradimes as possible while still providing a rich feature set.

Sometimes it is inevatible, in which case it is important to decide whether or not this feature should really be shipped
with the language. The feature may work better as a standalone package instead.

***The library should only be as opinionated as the language itself.***

## Make the feature friendly

This is important. There should be plenty of tools in place to create quick examples and provide room
for lots of modification without complete overhaul.

It should also not force to user to clean up memory themselves without somehow marking such features as
unsafe.

## Should work in-tandem with the rest of the standard library.

Your new feature should feel like it fits into the rest of the stdlib. It shouldn't feel like its seperate or antithetical to
the languages goals or design.

## Should be cross-platform

Functionality must have an equivalent version for every operating system without creating
significant tradeoffs for the users.

This may be impossible. In certain cases when binding OS level functionality, some Operating system
have more features than others. In these cases, it is best to properly document it and ensure that it
is extremely difficult for the user to get wrong.

## Should solve a common problem (or bind OS behavior)

The feature shouldn't be a very specific use case. For example a fully fledged game engine might be
too hyper-specific to include in the standard library. AI tools are another example. These things
are best left to being seperately distributed packages.

## Should be safe

This feature shouldn't open up large security vulnerabilities without the user's knowledge.

Some things are always going to be slightly unsafe, but these things should always make their unsafe nature known.

## Should have a small footprint

The feature shouldn't eat up tons of memory, cpu, or disk space. The exception may be for things that are necessarily
hard for the computer to do. Some examples may include file compression and decompression.

## Should have no external dependencies

Self explanitory.

## Should be pushed with tests

Push your changes with tests to those changes.

---

# Naming convention and styling

Like before, these are guidelines, not hard rules. If it is best to break them for clarity, usability, or performance, then do so.
Be prepared to justify any rule breaking you do.

## Constructors for structs

Constructors should be have a the name self. There can also be several version of the constructor.
Constructors should avoid returning possible errors or optionals. A constructor should be able to be called
without the posibility of failing.

## Magic Values

Avoid the use of magic values. When these are required you should put them inside a struct or declare them as
constants at the top of the module.

## Casing

This is similar to python's PEP8.

|          Unit          |        Style       |  Example  |
|:----------------------:|:------------------:|:---------:|
|Function/member/variable|  lower_snake_case  | get_data  |
|  Struct/Enum/Protocol  |     PascalCase     |HTTPServer |
| constant/Enum Variant  |SCREAMING_SNAKE_CASE|LARGESTSIZE|
|     Package/Module     |     camelCase      |regexParser|

## Import location

Imports currently don't care where they are placed. They don't actually effect the AST in any significant way, they just tell the compiler that there is more work to do and to include this new module inside the currently parsing one's list of imports.

All of this said, you still shouldn't put imports anywhere other than the top of the file. It makes it immediately clear what this file depends on without needing to scroll.

Don't send me cursed code with imports 200 lines down inside of enum definitions. Although it is valid code, it is still cursed.

## Packaging

When there are several layers of complexity it may be best to use packages and subpackages to encapsulate the modules. For example, if you were to have:
```
http/
   | server/
   |   - someModule.bcl
   |   - all.bcl
   |
   | client/
   |   - someOtherModule.bcl
   |   - all.bcl

   - protocol.bcl
   - all.bcl
```

Don't over-package, overly-nested namespacing is incredibly annoying and verbose. Packages should be used sparingly, but not completely avoided.

This topic is mainly just opinion, so there is a lot of room here for creativity. Do whatever you think will make other programmers happy :)

## Don't overuse `public`

`public` is great. It's what we need for any module to be useful.Just note that it can be overused and expose vulnerabilities or safety issues. Implementation details that are tightly coupled to other moving parts should not be made public. Only your "user-land" functions should be made public. Internal details (most of the time) do not and should not be exposed.

The default visibility is `private` for a reason.

## Use common sense
<!-- |||
|-|-|
| -->