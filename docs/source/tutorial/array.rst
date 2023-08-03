Arrays
=======

Arrays are a simple "aggregate data type". This just means it hold multiple items.

Arrays have these attributes:

* Can be indexed (indexes start at 0)
* Mutable (data can be changed)
* Fixed size
* elements only have 1 type. Cannot mix data types.

Arrays can only hold a specific number elements. This number cannot be changed later.
If your array holds 12 items, then it can never hold more than or less than 12 items.

########################
Defining a Simple Array
########################

This can be done in two ways

Firstly: Giving every element a value
--------------------------------------

.. code-block:: bcl

    import stdlib::*;

    define main() {
        x = [0, 1, 2, 3, 4, 5, 6];
    }


Secondly: Repeating an expression N times
------------------------------------------

This method involves recomputing some expression :code:`N` times to create
an array of size :code:`N`.

Note, I say **recomputing** for a reason. This doesn't simply copy the value.
This will rerun the code for each element.

.. code-block:: bcl

    import stdlib::*;

    define main() {
        // an array with 7 elements
        x = [0; 7];
    }

.. note::

    Doing something like this will result in 10 random numbers,
    not 1 random number repeated 10 times.

    .. code-block:: bcl

        import stdlib::*;
        import math::*;

        define main() {
            x = [random(); 10];
        }


##################
Indexing an Array
##################

Indexing an array lets you get or change the value of a specific item

Getting the value
------------------

.. code-block:: bcl

    import stdlib::*;

    define main() {
        x = [2, 4, 6, 8, 10, 12, 14];

        println(x[0]); // gets the number 2 from the index "0" in the array.
    }

Setting the value
------------------

.. code-block:: bcl

    import stdlib::*;

    define main() {
        x = [2, 4, 6, 8, 10, 12, 14];

        x[0] = 333;

        println(x[0]); // gets the number 333 from the index "0" in the array.
    }

####################
Looping Over Arrays
####################

Remember when I was talking about items when I went over the for-loop?
Well, arrays have items, we can iterate over these items!

.. code-block:: bcl

    import stdlib::*;

    define main() {
        x = [2, 4, 6, 8, 10, 12, 14];

        for i in x {
            println(i);
        }

        // This will print our entire list
        // an item will be printed on each line.
    }

.. note::

    Changing :code:`i` will not change the original item in the array.
    It will only change the value of your :code:`i` variable.

    The loop coppied the item!

###################
Getting the Length
###################

Sometimes remembering the length is annoying, and sometimes you want it changed.
To make your life easier, you can use :code:`.length`.

the :code:`.` here is the "member access operator". A member is some data a value can have.
You will learn more about members in a later unit.

.. code-block:: bcl

    import stdlib::*;

    define main() {
        x = [2, 4, 6, 8, 10, 12, 14];

        // if there are too many dots for your liking,
        // you can put parens like this: 0..(x.length)
        // it can give you more visual clarity
        for i in 0..x.length {
            // double the value of x[i] and then store
            // it back into x[i]
            // i is our index
            x[i] *= 2;
        }

        // This will print our entire list
        // an item will be printed on each line.
        for i in x {
            println(i);
        }
    }

###############
Passing Arrays
###############

Some of you may have been wondering how we write the type of an array. This is necessary for
passing arrays to functions.

.. code-block:: bcl

    import stdlib::*;

    // Our "array" argument is an array of i32's that is 7 elements long
    // This function also returns an array of i32's that is 7 elements long
    define double_the_array(array: i32[7]) -> i32[7] {
        for i in 0..(array.length) {
            array[i] *= 2;
        }

        // array is a copy, so we can return out modifications as a new array
        return array;
    }

    define main() {
        x = [2, 4, 6, 8, 10, 12, 14];

        // set x to the result of our function
        x = double_the_array(x);
    }