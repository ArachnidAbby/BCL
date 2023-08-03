Variables
==========

Variables are a way to store data for later access or modification.
Variables are only accessible inside of the scope they were defined in.

.. code-block:: bcl

    define main(){
        my_var = "foo"; // type-inference makes this variable a string
        my_var = 9; // will throw an error, we already declared that my_var is a string

        println(my_var);
    }

-------------------------
explicit type definition
-------------------------

.. code-block:: bcl

    define main(){
        my_var: string = "foo";
        my_var2: i32 = "bar"; // will throw an error, the value is of the wrong type.

        println(my_var);
    }

---------------------
assignment operators
---------------------

This is a list of all the different types of assignment.

.. list-table:: types of assignment
    :widths: 25 25
    :header-rows: 1

    * - symbol
      - description

    * - `+=`
      - addition assignment
    * - `-=`
      - subtraction assignment
    * - `*=`
      - multiplication assignment
    * - `/=`
      - division assignment
    * - `=`
      - normal assignment

------
Scope
------

The best way to explain variable scope is by example

.. code-block:: bcl

    define main() { // scope 1
        foo = 12; // defined in scope 1

        { // scope 2
          bar = 15; // defined in scope 2
          println(foo); // no issues since scope 2 is *inside* scope 1
        }

        println(bar); // throws a compile time error
    }