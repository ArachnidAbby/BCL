Functions
==========

Functions use a keyword to be defined.


.. code-block:: bcl

    define myfunc() {
        println("I did some things!");
    }

*************************
returns and return types
*************************

.. code-block:: bcl

    define myfunc() -> int{
        return 9;
    }

**********
arguments
**********

.. code-block:: bcl

    define add(x: int, y: int) -> int {
        return x+y;
    }
