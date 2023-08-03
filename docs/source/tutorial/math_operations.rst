Math Operations
================

There are different kind of math operations in BCL.


###########################################
Here is a list of all the math operations
###########################################

Order of operations does apply. If you aren't sure what the order will be when compiled,
then you can put some expressions in parenthese, :code:`(10+10) * 2` for example.


* Multiplication :code:`*`
* Division :code:`/`
* Subtraction :code:`-`
* Addition :code:`+`
* Exponentiation (raise to a power) :code:`**`
* Is equal to :code:`==`
* Is not equal to :code:`!=`
* Is less than :code:`<`
* Is greater than :code:`>`
* Is less than or equal to :code:`<=`
* Is greater than or equal to :code:`>=`

----------------
Logic Operators
----------------

These work on boolean (see section on data types).
Although, nearly all types do have a "truthiness". This just determines what a value should become if we
want it to act like a boolean. For example, ints are truthy if not zero, otherwise they are falsey.

* And :code:`and`
* Or :code:`or`
* Not :code:`not` (prefix)

---------------------------
Stuff we learn about later
---------------------------

* Indexing :code:`[index]` (postfix)
* Reference :code:`&` (prefix)
* Dereference :code:`*` (prefix)
* Namespace :code:`::`

Bitwise operation
^^^^^^^^^^^^^^^^^^

These work on bits directly. These work like logic gates for each bit (except for left and right shift).

* Xor :code:`^`
* And :code:`&`
* Or  :code:`|`
* Left Shift :code:`<<`
* Right Shift :code:`>>`
* Not :code:`~` (prefix)

####################
Order of Operations
####################

This works like PEMDAS. If something appears first in this list, the compiler will do it first.

.. list-table:: Operations
    :widths: 30 30 20
    :header-rows: 1

    * - Operation(s)
      - example
      - associativity

    * - Parenthese :code:`()`
      - :code:`(5+5)`
      - N/A

    * - Namespace :code:`::`
      - :code:`stdlib::println`
      - left

    * - Dereference :code:`*`
      - :code:`*my_reference`
      - left

    * - | Access Member :code:`.`,
        | Index :code:`[]`

      - | :code:`var.member`,
        | :code:`var[index]`

      - | left,
        | left

    * - Reference :code:`&`
      - :code:`&x`
      - left

    * - Cast :code:`as`
      - :code:`22 as i8`
      - left

    * - Exponentiation :code:`**`
      - :code:`2**6`
      - **right**

    * - Bitwise Not :code:`~`
      - :code:`~(-255)`
      - N/A

    * - | Modulo :code:`%`,
        | Div :code:`/`,
        | Mul :code:`*`

      - | :code:`10 % 2`,
        | :code:`22 / 11`,
        | :code:`2 * 15`

      - | left,
        | left,
        | left,
        | left

    * - | Sum :code:`+`,
        | Sub :code:`-`

      - | :code:`8 + 9`,
        | :code:`10 - 4`

      - | left,
        | left

    * - | Left Shift :code:`<<`,
        | Right Shift :code:`>>`

      - | :code:`69<<2`,
        | :code:`420>>2`

      - | left,
        | left

    * - | Bitwise And :code:`&`,
        | Bitwise Xor :code:`^`

      - | :code:`4&5`,
        | :code:`4^5`

      - | left,
        | left

    * - Bitwise Or :code:`|`
      - :code:`4|5`
      - left

    * - | Is Equal To :code:`==`,
        | Not Equal To :code:`!=`,
        | Less Than or Equal To :code:`<=`,
        | Greater Than or Equal To :code:`>=`,
        | Less Than :code:`<`,
        | Greater Than :code:`>`

      - | :code:`==`,
        | :code:`!=`,
        | :code:`<=`,
        | :code:`>=`,
        | :code:`<`,
        | :code:`>`

      - | left,
        | left,
        | left,
        | left,
        | left,
        | left

    * - Logic Not :code:`not`
      - :code:`not true`
      - N/A

    * - Logic And :code:`and`
      - :code:`true and false`
      - Left

    * - Logical Or :code:`or`
      - :code:`true or false`
      - left

    * - | Assignment Sum :code:`+=`,
        | Assignment Sub :code:`-=`,
        | Assignment Div :code:`/=`,
        | Assignment Mul :code:`*=`

      - | :code:`x += 12;`,
        | :code:`x -= 12;`,
        | :code:`x /= 12;`,
        | :code:`x *= 12;`

      - | N/A,
        | N/A,
        | N/A,
        | N/A
