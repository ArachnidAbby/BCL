Variables
==========

.. code-block:: bcl

    define main(){
        my_var = "foo"; // type-inference makes this variable a string (string-literal until modified)
        my_var = 9; // will throw an error, we declared that my_ver was a string previously

        println(my_var);
    }

-------------------------
explicit type definition
-------------------------

.. code-block:: bcl

    define main(){
        my_var  : string = "foo"; // type-inference makes this variable a string (string-literal until modified)
        my_var2 : int = "bar"; // will throw an error, the value is of the wrong type.

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
