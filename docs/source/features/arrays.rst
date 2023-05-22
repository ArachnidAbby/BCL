Arrays
=======

Arrays are an :code:`aggragate data type` that can store a fixed number of elements of a fixed type.

.. important::

    You must import :code:`stdlib` or define :code:`printf(strlit, ...)` and :code:`exit(i32)` to use variable index

##############
instantiation
##############

.. code-block:: bcl
    
    define main() {
        x = [0, 1, 2, 3, 4, 5]; // variable `x` is of type `i32[6]`
    }

or, alternatively:

.. code-block:: bcl
    
    define main() {
        x = [0; 6]; // variable `x` is of type `i32[6]`
    }


################
indexing arrays
################

To get a value inside an array, you need to :code:`index` it. Index's start at :code:`zero` and not at one.

.. code-block:: bcl

    define main() {
        x = [0, 1, 2, 3, 4, 5]; // variable `x` is of type `i32[6]`
        println(x[2]); // get value at index 2 (the number `2` in this case.)
    }


############################
putting a value at an index
############################

To get a value inside an array, you need to :code:`index` it.

.. code-block:: bcl

    define main() {
        x = [0, 1, 2, 3, 4, 5]; // variable `x` is of type `i32[6]`
        x[3] = 16; // replace value at index 3 with 16
    }
