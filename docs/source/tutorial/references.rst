References
===========

References are pointers to locations in memory where some data is stored.
We can use these in things like functions to have them modify data coming into them.

Usually, when data is passed around, it is copied. This means modifying it will not affect the original.

###########################
How are references written
###########################

References use the reference operator (:code:`&`).
This is used not only for when refering to a reference type (:code:`&i32`),
but also to reference some variable (:code:`&my_variable`).

If you try to reference something not in a variable (:code:`&69420`), a temporary variable will be created for you.
You cannot actually refer to this by name, so if you lose the reference, you can't write
data to that location.

#############
Side Effects
#############

A side effect is an effect a function has on the global state of the program or the variables passed into it.
This can be something as simple as modifying some element in a array.

.. note::
    Technically, using :code:`println` has a side-effect, it modifies the "standard out".


.. code-block:: bcl

    import stdlib::*;

    // my_array_ref is a reference to an int32 array with 5 elements in it.
    define set_data(my_array_ref: &i32[5], index: i32, new_data: i32) {
        my_array_ref[index] = new_data; // has side-effects, because it modifies a referenced value
    }

    define main() {
        my_array = [0; 5]; // init array with 5 elements, all elements = 0

        println(my_array[2]);

        set_data(&my_array, 2, 69420); // referencing my_array and passing it in with the other args

        println(my_array[2]); // should print "69420"
    }

###############
De-referencing
###############

Often times, a reference will automatically be dereferenced. This isn't always the case!
So often, we may want to derefence to get a copy of the value. We can use the derefence operator (:code:`*`)

.. code-block:: bcl

    import stdlib::*;

    define main() {
        x = 22;
        y = &x; // y contains a reference to x. This is called "aliasing". More on that later!
        z = *y; // z now contains a copy of what y was referencing. so x == 22;
    }

############################
Lifetimes and Returnability
############################

References are assumed to be local to a function. The memory that they reference will be cleaned up
after a function finishes running, so we cannot return them. The only exception to this is if they have
a long lifetime. This happens when you pass references into functions as arguments.

**This works**

.. code-block:: bcl

    import stdlib::*;

    // my_array_ref is a reference to an int32 array with 5 elements in it.
    define set_data(my_array_ref: &i32[5], index: i32, new_data: i32) -> &i32[5] {
        my_array_ref[index] = new_data; // has side-effects, because it modifies a referenced value

        // we can return this because we know it lives longer than the function call.
        return my_array_ref;
    }

    define main() {
        my_array = [0; 5]; // init array with 5 elements, all elements = 0

        println(my_array[2]);

        set_data(&my_array, 2, 69420); // referencing my_array and passing it in with the other args

        println(my_array[2]); // should print "69420"
    }


**This doesn't**

.. code-block:: bcl

    import stdlib::*;

    define return_some_ref() -> &i32 {
        // reference a local constant ('&22'),
        // this gets cleaned up when the function finishes running, so we cannot return a reference to it.
        return &22;
    }

    define main() {
        x = return_some_ref();
    }

.. warning::
    Lifetime inference is a little broken. Aliasing lets you get around much of the safety
    restrictions that are put into place to ensure you cannot access memory after it has been freed.
    Avoid aliasing at all costs! This will be fixed as soon as possible, but it requires heavy modification of
    how the language represents types under the hood. So please be patient and use references responsibly.
