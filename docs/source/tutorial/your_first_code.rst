Your First Project
===================

.. tip::

    If you are new to programming/coding, then you should follow along with **all**
    code examples. Later you should use the new knowledge in small projects. Try to do everything
    at your own pace and try to do things *without help* first, then if you are stuck, get help.

    Just note, that you don't have to make ground-breaking projects. They can be as simple as a
    calculator or a simple texted based, Cookie-Clicker-like game.

    If you need more time than what the tutorial provides, then take that time. Take breaks frequently if
    you are struggling to force yourself to code. Coding is hard sometimes. Sometimes what's best is a break.

#######
Step 1
#######

Firstly you need to have BCL installed.

After that you must create a new file with any name, just make sure it ends with :code:`.bcl`

In this example we will use :code:`main.bcl`

########################
Step 2: Write your code
########################

For now you can copy and paste this into your file. We want to verify that the language works on your machine.

If there are any problems, feel free to join the `discord server <https://discord.gg/R76Egy4uXs>`__ for support or
open an issue on the `github page <https://github.com/spidertyler2005/BCL>`__. This could very well be a bug on our end.

.. note::

    :code:`{` is the opening of a block of code.

    :code:`}` is the end of a block of code.

    We use these when declaring a function.

    :code:`;` is used to say "we are done with this line of code".
    It can also be thought of as "I've finished this statement". Without putting a semicolon you can get bugs.
    One you might encounter is something like "type Void is not callable". This happens because function calls
    an also be written like this :code:`println "hello world";`.

.. code-block:: bcl

    // give us access to plenty of handy functions
    import stdlib::*;

    // the "main" function is the entry point for your program
    // this is what gets run when you run your code.
    define main() {
        println("Hello World");
    }

########################
Step 3: Compile and Run
########################

Currently compilation in BCL is a little complicated.
As time progresses, this will become easier and easier.

To compile and execute at the same time, we can run the command:
:code:`bcl compile main.bcl --emit-binary --run`

If you want to know more about how the :code:`bcl` command works, then try doing:
:code:`bcl help`
