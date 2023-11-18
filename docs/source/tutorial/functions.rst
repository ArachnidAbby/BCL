Functions
==========

Functions are a way to avoid repeating blocks of code. They can be very helpful!
We have actually already used several! Functions work similarly to how they work in math.

###################
Calling a Function
###################

We have already done this serveral times!
Let me show you.

.. code-block:: bcl
    :emphasize-lines: 4

    import stdlib::*;

    define main() {
        println("Hello World");
    }

Yes, that is a function call!
We tell the language we want to "call" code from the function :code:`println`. We are then "passing" in the arguments
inside of those parenthese. We are passing a single argument, a strlit.

-----------------------------
Other Ways to Pass Arguments
-----------------------------

BCL doesn't require you to use parenthese when calling a function unless you are passing several arguments.

Let me show you a few ways you can call a function.

.. code-block:: bcl
    :emphasize-lines: 5,6,10,11

    import stdlib::*;
    import math::*;

    define main() {
        "Hello World".println();
        println "Hello Again";

        // a function from math.bcl
        // returns the smallest number from the 2 passed in
        10.min 12;
        10.min(12);
    }

-----------------
Function Returns
-----------------

Some functions give you a value back after calling them, this is called a "return value".
Let me give you an example to try!

.. code-block:: bcl
    :emphasize-lines: 5,10

    import stdlib::*;
    import math::*;

    define main() {
        x = min(10, 12); // storing the return value in x
        println(x);

        // showing how we can put expressions anywhere they
        // are accepted.
        println(min(22, 20));
    }

Give it a try and see what output you get!

----

############################
Defining Your Own Functions
############################

Functions can be defined by you too. Like before, we have already done this!
|

Here is a simple example.

.. code-block:: bcl
    :emphasize-lines: 4,5,6, 9

    import stdlib::*;

    // defining our function
    define say_hi() {
        println("Hi!");
    }

    define main() {
        say_hi(); // calling our function
    }

----------------
Using Arguments
----------------

When defining functions, you can ask the caller to pass in some data.
Arguments are how we do this. They act as variables in side the function.

.. code-block:: bcl
    :emphasize-lines: 6, 11

    import stdlib::*;

    // the function has two arguments
    // x is an i32 (a whole, integer number)
    // y is an i32 too
    define add_numbers(x: i32, y: i32) {
        println(x + y);
    }

    define main() {
        add_numbers(10, 20); // calling our function
    }

.. note::

    Data is coppied into the function when called, you cannot modify variables
    that the caller has passed in, you are just given a copy of the data.

---------------
Returning Data
---------------

We can also give data back to the caller using the :code:`return` statement.

.. code-block:: bcl
    :emphasize-lines: 7, 11

    import stdlib::*;

    // the function has two arguments
    // x is an i32 (a whole, integer number)
    // y is an i32 too
    define add_numbers(x: i32, y: i32) {
        return x+y;
    }

    define main() {
        result = add_numbers(10, 20); // calling our function
        println(result);
    }

One important thing to note about return is the fact that it tells
the function to immediately stop running while also giving back a value to the caller.

Let me give you an example.

.. code-block:: bcl

    import stdlib::*;

    define add_numbers(x: i32, y: i32) {
        return x+y;

        println("I won't be run!");
    }


###########
Side Notes
###########

Functions can be confusing for some. Which I can understand. It took me several months to learn how return works
when I first started writing code. It is an important concept so do take the time to learn it!

And, do note, that functions will get slightly more complicated later on. Specifically when we learn about methods
and generators. For now, don't worry about those.