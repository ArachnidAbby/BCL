Variables
==========

In this lesson we will cover the basics of variables and datatypes.

A variable is a way to store data for later use. Variables can be changed (they are mutable) at any time.
One of the only limitations of a variable is that it must store the same kind of data at all times. It cannot store
your laundry list, then store your age, it can only store one *type* of data.

##########################
Defining a basic variable
##########################

.. code-block:: bcl

    import stdlib::*;

    define main() {
        // creates a new variable called "name"
        name = "Ricky Bobby";

        // prints without creating a new line
        print("Hi my name is: ");

        // prints the value inside of the name variable
        println(name);
    }

.. tip::

    Be sure to use descriptive variable names. This can avoid confusion.

#################################
Changing the value of a variable
#################################

This is no different than declaring a variable!

.. code-block:: bcl

    import stdlib::*;

    define main() {
        // creates a new variable called "name"
        name = "Ricky Bobby";

        // prints without creating a new line
        print("Hi my name is: ");

        name = "Bobby Ricky";

        // prints the value inside of the name variable
        // this will now print "Bobby Ricky"
        println(name);
    }


##########################
Doing math with variables
##########################

Variables can be used in math expressions, just like any other value/expression.

.. code-block:: bcl

    import stdlib::*;

    define main() {
        // creates a new variable called "name"
        age = 10

        // prints without creating a new line
        print("Hi, I am ");
        print(age);
        println(" years old");

        age = age + 10;

        print("Hi, I am now ");
        print(age);
        println(" years old");
    }

.. note::

    Math expresions can go anywhere where we are putting:

    * variables
    * numbers
    * strings (The stuff in quotes)

The next lesson has a full list of different math operations in BCL.

----

###########
Data types
###########

Data types are how we tell the computer what kind of data we are trying to represent.
All the computer sees are individual bits and bytes of data, it doesn't care what the data actually is.

The compiler controls what we are allowed to do with certain pieces of data based on the datatype.
If we do something wrong, the compiler can tell us what we did and where we did it.

------------------
Builtin datatypes
------------------

These datatypes are hard-coded into the language itself. You won't find their definition anywhere
in the :doc:`standard library </standard_library/index>` (Code we package with the language).

.. tip::

    Alot of these types have different sizes. I would suggest sticking to 32 bits for ints and floats.
    If you need larger numbers or percision, use 64 bits. If you want small values and to save memory, use smaller sizes.
    decimal numbers default to f32. Ints default to i32.

* signed integers (whole numbers that can be positive or negative) :code:`i8, i16, i32, i64`
* unsigned ints (whole numbers that are only positive) :code:`u8, u16, u32, u64, size_t`
  (size_t is either u32 or u64 depending on the system being x86 or x64)
* floating point numbers (decimal numbers) :code:`f32, f64`
* string literal :code:`strlit`
* booleans (:code:`true` or :code:`false` values) :code:`bool`

Array type
^^^^^^^^^^^

An array is an aggregate data type. That means it can hold multiple pieces of data.
An array type looks like this :code:`type[size]`. Here is an example: :code:`i32[420]`
We will have an entire unit about arrays, so don't worry if you are confused.

References/Pointers
^^^^^^^^^^^^^^^^^^^

.. tip::

    Memory refers to your computers RAM, not your hardrive's storage.
    Memory is split up into different addresses (just a number) and
    each address holds 8 bits (1 byte) of information. There are exceptions to this, but generally
    this is how it works. You can think of a pointer like having the address to someone's house, but
    not actually having the house itself. You know where you can find the house, but you yourself do not
    have the house.

References point to a piece of data that exists somewhere else in your computers memory. References can be confusing.
Most times in the language, a reference is automatically "dereferenced" meaning we go out and get that data which is pointed to.
Sometimes, it isn't, this is in places like function calls.

If this is confusing, don't worry, we will have a seperate lesson on it. It isn't super important for beginners.

UntypedPointer
^^^^^^^^^^^^^^^

.. warning::

    This is the language's goto way of having unsafe behavior. Often times
    you won't want to interact with this directly.

UntypedPointer is a way to accept any arbetrary pointer type in a function. UntypedPointer is also returnable regardless
of the data's lifetime. You can't directly do anything with UntypedPointer, but you can cast it to any other pointer type.
This means you can use it as ANY kind of data. That is what makes it so unsafe.

This type is used in a few places in the standard library, but all of the unsafe behavior that it wraps around is hidden
from the user. This means it is safe to use these types and functions.

**Do not worry about UntypedPointer until you have an advance understanding of programming and computers!**

Range
^^^^^^

Ranges are an "iterable" type. That means you can use them in :code:`for loops`. We will learn about these in the future.

Void
^^^^^

Void isn't really a type. It is a way to say "I have no type". That's why you can't directly use void anywhere in the language.
You can't even refer to void, the language will say it doesn't exist if you try to use it.

The :code:`println` function returns Void, which is to say it doesn't return anything. It gives you no data back.

----

####################################
Explicitly giving a variable a type
####################################

You can tell a variable to be a specific type. You can only do this the first time you declare it.

.. important::

    You cannot "Shadow" variables in BCL. This just means two *different* variables in the same scope
    cannot share the same name.


.. code-block:: bcl
    :emphasize-lines: 7

    import stdlib::*;

    // We need this for the "pow" operation
    import math::*;

    define main() {
        big_number: i64 = 2**10; // 2 raised to the 10th power.

        // printing out big number
        println(big_number);
    }

BCL will automatically convert between datatypes if necessary and if possible.
We can't convert a string to an int for example. But, a smaller int can be automatically
converted to a bigger one.

###############
Variable scope
###############

Variables exist only ***after*** first being declared. They can be accessed from the same code block
or codeblocks that are nested inside the one it was defined in. Once a code block finishes being run,
it's variables become invisible and no longer exist. Although, do note, they won't be freed from memory until
the function returns/finishes running.

.. code-block:: bcl

    define main() {
        x = 10;

        {
            // x is available here
            println(x);
            x = 15;
        }
        println(x);

        {
            y = 22;
        }

        // The compiler will throw an error
        // it will tell you y doesn't exist!
        println(y);
    }