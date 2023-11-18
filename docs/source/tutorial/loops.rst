Loops
======

Loops are a simple way to repeat a block of code.
There are *two* kinds of loops.

* A conditional loop (a "while" loop) - Loops as long a condition is true
* A data loop (a "for" loop) - For each item in some data, it will loop and yield the next item.

############
While Loops
############

We will start with the simpler while loop.

A while loop checks if a condition is true, if it is then it will run a block of code.
The checks repeat after the block of code is run. If the condition is false, the looping stops.

.. code-block:: bcl

    import stdlib::*;

    define main() {
        x = 0;

        while x < 10 {
            println(x);
            x = x + 1;
        }
    }

This code will count from 0 to 9!

.. tip::

    We can also use :code:`x += 1;` to increment x.


##########
For Loops
##########

A For-loop will check if another item is available in some "iterable".
If an item is available then it will store that value and run the block of code.
This repeats until it runs out of items.

.. code-block:: bcl

    import stdlib::*;

    define main() {
        // 0..10 is a "range literal". Just saying we want an iterable that counts from 0 to 9.
        for x in 0..10 {
            // a variable "x" is created
            // each time the loop runs, x is given the next value
            println(x);
        }
    }

This code will count from 0 to 9!