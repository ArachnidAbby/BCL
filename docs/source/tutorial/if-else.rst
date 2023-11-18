If and Else statements
=======================

.. role:: bcl(code)
   :language: bcl
   :class: highlight

If and Else statements take a boolean and based on the value will run some code.
Basically, its a way to conditionally run some code.

examples of some uses:

* Give the user a different greeting if they have a specific name
* Only allowing entry to someone over the age of 18
* Making a quiz
* Moving a player character if a certain key has been pressed

These control flow statements are the crux of programming. They are what really make
complex logic possible.

#############
If Statement
#############

An if-statement works by saying "if this condition is true, run this code".

.. code-block:: bcl

    import stdlib::*;

    define main() {
        if 8 == 8 {
            println("eight does in fact equal 8.");
        }
    }

The code in the if-statement will only run if :bcl:`8==8` evaluates to :bcl:`true`.

.. code-block:: bcl

    import stdlib::*;

    define main() {
        name = "Monty";

        if name == "Monty" {
            println("Is your last name 'Python' by chance?");
        }

        println("I run regardless of the name!");
    }

###############
Else Statement
###############

An else-statement must come immediately after an if-statement. This is a block of
code that should only be run if the if statement failed.

.. code-block:: bcl

    import stdlib::*;

    define main() {
        name = "Monty";

        if name == "Monty" {
            println("Is your last name 'Python' by chance?");
        } else {
            println("You need a cooler name!");
        }

        println("I run regardless of the name!");
    }

#####################
Chaining else and if
#####################

If and Else can be chained to create more complex constructions, that looks like this.

.. code-block:: bcl

    import stdlib::*;

    define main() {
        name = "Monty";

        if name == "Monty" {
            println("Is your last name 'Python' by chance?");
        } else if name == "George" {
            println("Is your last name 'Washington' by chance?");
        } else {
            println("You need a cooler name!");
        }

        println("I run regardless of the name!");
    }

.. note::

    The whitespace isn't important! You can also write the above example with extra space.

    .. code-block:: bcl

        import stdlib::*;

        define main() {
            name = "Monty";

            if name == "Monty" {
                println("Is your last name 'Python' by chance?");
            }

            else

            if name == "George" {
                println("Is your last name 'Washington' by chance?");
            }

            else {
                println("You need a cooler name!");
            }

            println("I run regardless of the name!");
        }

    Some people might say it looks a little cursed like this, but it's your code.
    Just be careful when working on a team to follow their prefered styles.

####################
Multiple Conditions
####################

Sometimes you want to check for multiple conditions.
Sometimes you might also want to only run code if a condition is :bcl:`false`

We can use these following operations:

* :bcl:`cond1 and cond2` - checks if both conditions are true. If one is false, the output is false
* :bcl:`cond1 or cond2` - If on condition is true, the output is true, regardless of the other condition.
* :bcl:`not cond` - Gets the opposite of the boolean. False becomes true and true becomes False.

Here is an example of this being put to use.

.. code-block:: bcl

    import stdlib::*;

    define main() {
        name = "Bob";
        age = 22;

        // Try this: See if you can find a way to remove the "not"
        //           and still have it do the same thing.
        if (name == "Bob" or name == "Bill") and not age < 18 {
            println("Great name, and great to know you are an adult!");
        } else if age < 18 {
            println("Adult's only. Get out of here kid!");
        } else {
            println("You need a much better name to get into this club!").
        }
    }

.. tip::

    Sometimes you may want to split the condition onto several lines.
    This can make it easier to read. Just split it at a good location.