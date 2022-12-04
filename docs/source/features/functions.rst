Functions
==========

Functions are a way to define a "subroutine" that can be executed repeatedly.
Every function has it's own scope of variables independent of it's caller.


.. code-block:: bcl

    define myfunc() {
        println("I did some things!");
    }

******************
special functions
******************
The :code:`main` function is treated in a special way by the compiler. This function is the entry point for your program. 
There may only be ONE main function per program. Having zero :code:`main` functions or more than one will result in a compile-time error.


*************************
returns and return types
*************************

Functions can return a value of a specified type. This return value can be captured by the caller.

.. code-block:: bcl

    define myfunc() -> i32{
        return 9;
    }

    define main() {
        println(myfunc()); // println uses the returned value from calling myfunc()
    }

**********
arguments
**********

.. code-block:: bcl

    define add(x: i32, y: i32) -> i32 {
        return x + y;
    }
