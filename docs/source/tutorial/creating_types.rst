User Made types
================

Like most programming languages, Bcl lets you create your own types.

There are two kinds of types:

- Enumerations (enums)
- Structures (structs)

######
Enums
######

I think Enums are the easiest to understand because they are very simple.
The hardest part is finding a good use case.

Here are some example uses:

* Tile types in a tilemap
* HTTP header type
* A set of valid states a the program can be in

Enums let you limit the user's selections to some set of options. This lets you ensure
that someone cannot pass in invalid data.

Now, you may think enums are some kind of magic, but really, they are just integers!

-----------------
Defining an Enum
-----------------

Enums "enumerate" items meaning they count stuff. This just means each "variant" in the enum doesn't
need to be given a value, the language will do it for you!

.. code-block:: bcl

    enum States {
        // each item here is called a "variant"
        WORKING,  // language gives a value of 0
        BUGGY,    // language gives a value of 1
        CRASHING, // language gives a value of 2
        INVALID;  // language gives a value of 3
    }

Now, although enums can automatically generate ALL the values, sometimes you want to explicitly define
a variant as having a specific value.

.. code-block:: bcl

    enum States {
        // each item here is called a "variant"
        WORKING,  // language gives a value of 0
        BUGGY: 22,    // language gives a value of 22
        CRASHING, // language gives a value of 23
        INVALID: 42;  // language gives a value of 42
    }

.. note::

    Enums will automatically use the smallest sized integer it can
    get away with to represent the data. If you have large numbers or big enums,
    then the enum will be represented as a larger integer.

    You can get the size (in bytes) by doing :code:`MyEnumType::SIZEOF`.
    Just note, having a :code:`SIZEOF` as a variant will make it impossible to
    access that variant.


#############
Struct Types
#############

Stucts are another "aggregate" data type. That means they hold multiple items.

With a structure you define what kind of data you would like it to store. Structs
are a great way to package related data together. For example a user with an age and a grade level.
We want a user datatype that contains both pieces of information.

------------------
Defining a Struct
------------------

.. code-block:: bcl

    struct User {
        // these variables are called "members"
        age: i32,
        grade_level: i32; // we could swap this with an Enum type!
    }


-----------------------
Instantiating a Struct
-----------------------

Now, unlike an enum, you can't do anything with the type itself.
You must "instantiate" it to access the data.

Instantiation means that we create some data of a type (usually a struct type).


.. code-block:: bcl
    :emphasize-lines: 9

    struct User {
        // these variables are called "members"
        age: i32,
        grade_level: i32; // we could swap this with an Enum type!
    }

    define main() {
        // This is a weird use of a block "{}", but
        // this is the syntax.
        my_user = User {age: 12, grade_level: 8};
    }

.. note::

    You must give *every* member a value to instantiate
    a struct.

---------------------------
Getting Data From a Struct
---------------------------

Now, what makes a struct useful is that we can get data back out of it.
We can also store data into it. Each instance holds seperate data, but follows the same
schematic. That means they all have the same members.

.. code-block:: bcl
    :emphasize-lines: 14, 24, 25

    import stdlib::*

    struct User {
        // these variables are called "members"
        age: i32,
        grade_level: i32; // we could swap this with an Enum type!
    }

    define main() {
        // This is a weird use of a block "{}", but
        // this is the syntax.
        my_user = User {age: 12, grade_level: 8};

        my_user.age = my_user.age + 2;
        my_user.grade_level = user.grade_level + 2;

        // Creating a second instance with different data
        your_user = User {age: 10, grade_level: 6};

        your_user.age = your_user.age + 2;
        your_user.grade_level = user.your_user + 2;

        println("My User");
        println(my_user.age);
        println(my_user.grade_level);

        println("Your User:");
        println(your_user.age);
        println(your_user.grade_level);
    }


#############################
Where Can We Use These Types
#############################

These user-defined types can be used **anywhere** a normal type can be used.
You can use them in arrays, function definitions,  and even other user-defined types!
These have tons of applications and have the exact same support as every other kind of type.

In a later tutorial, we will discuss more advanced constructions of structs. Things like methods,
visibility, and operator overloading. These are important for higher level programming.