Modules and Imports
====================

You may have noticed that as you write code, your source file can get pretty big!
What if we could seperate certain behaviors out into their own files. Well, like with most languages, we
can use what are called :code:`modules`.

#################
What is a module
#################

A module is just a file with code in it! Thats it!

Technically you have already been using them!

#################################################
Using multiple modules with the Import statement
#################################################

We can use the :code:`import` statement to tell the language that
we would like to access code from another module.

:code:`stdlib` and :code:`math` are actually both modules! They have several functions
defined for you. Things like :code:`println` are actually predefined functions.

##########################
Modules & Imports example
##########################

Let me show you an example. This example **Will NOT** compile.

.. code-block:: bcl

    // myModule.bcl
    import stdlib::*; // import everything into the global namespace (for this module)

    /// Gets the max representable number for a binary number of `x` length.
    define do_a_cool_thing(x: i32) -> i32 {
        return 2**x - 1;
    }


.. code-block:: bcl

    // main.bcl
    import myModule::*;

    define main() {
        do_a_cool_thing(5); // this function is not public! we can't use it!!!
    }

If you try this code, it should tell you that :code:`do_a_cool_thing` is private and cannot be accessed.

This is because we also need to use the :code:`public` keyword. This is used on *type definitions*, *function definitions*,
and *member definitions*. It exposes these names to other modules, by default functions and types are private,
which means they can only be accessed in the module they were defined in. This is to prevent exposing internal workings
to every user of a module. This also lets you protect data for a variety of reasons.

###########################
Visibilty & :code:`public`
###########################

:code:`public` is the only visibility keyword in BCL. It is the only one you will need because by default, everything is private.

Let me show you how to use it!


.. code-block:: bcl

    // myModule.bcl
    import stdlib::*; // import everything into the global namespace (for this module)

    // public type
    public enum MyEnum {
        VARIANT1, // these don't need to be public
        VARIANT2;
    }

    // public type
    public struct MyStruct {
        public a: i32, // public member
        public b: i32, // public member
        c: MyEnum; // private member
    }

    /// Gets the max representable number for a binary number of `x` length.
    public define do_a_cool_thing(x: i32) -> i32 {  // public function
        return 2**x - 1;
    }

    public define new_MyStruct(a: i32, b: i32) -> MyStruct {
        return MyStruct {
            a: a,
            b: b,
            c: MyEnum::VARIANT1
        };
    }


.. code-block:: bcl

    // main.bcl
    import stdlib::*;
    import myModule::*;

    define main() {
        // // this wont work, c is private!
        // x = MyStruct {
        //         a: 12,
        //         b: 55,
        //         c: MyEnum::VARIANT1
        //     };

        // Instead we use:
        x = new_MyStruct(12, 55);

        // accessing public members is perfectly fine
        println(x.a);
        println(x.b);

        // // But we CANNOT access private members
        // println(x.c);

        do_a_cool_thing(5); // this function IS public, we can use it!
    }

#################
Naming Collision
#################

Sometimes, modules can define the same functions! This can cause a naming collision.
This will cause the language to just pick whichever version of the function it wants to use, from whichever module
it wants. This is mostly randomly.

To prevent this, we can use namespacing. Modules have namespaces that can be accessed in the same way we access enum variants.
That is by using the namespacing operator (:code:`::`). This lets us specify which module we want to get the function from.

.. tip::
    You should usually default to using namespaces and not *"star imports"*. The exception usually being things like the
    modules in the standard library.

.. code-block:: bcl

    // myModule.bcl
    import stdlib::*; // "star import"


    public enum MyEnum {
        VARIANT1, // these don't need to be public
        VARIANT2;
    }

    public struct MyStruct {
        public a: i32, // public member
        public b: i32, // public member
        c: MyEnum; // private member
    }

    /// Gets the max representable number for a binary number of `x` length.
    public define do_a_cool_thing(x: i32) -> i32 {
        return 2**x - 1;
    }

    public define new_MyStruct(a: i32, b: i32) -> MyStruct {
        return MyStruct {
            a: a,
            b: b,
            c: MyEnum::VARIANT1
        };
    }


.. code-block:: bcl

    // main.bcl
    import stdlib::*;
    import myModule; // Not including it into the global namespace.

    define main() {

        // accessed using namespacing
        x = myModule::new_MyStruct(12, 55);

        // accessing public members is perfectly fine
        println(x.a);
        println(x.b);

        // accessed using namespacing
        myModule::do_a_cool_thing(5);
    }