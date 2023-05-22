Standard functions
===================

This is a list of all standardized functions and what they do.

.. note::

  These are all available in the :code:`stdlib` module

.. list-table:: standard functions
    :widths: 50,80
    :header-rows: 1

    * - function
      - description

    * - :code:`println(x: i32|strlit|f32|i64|f64)`
      - Prints to the standard output with a newline.

    * - :code:`print(x: i32|strlit|f32|i64|f64)`
      - Prints to the standard output

    * - :code:`printf(x: strlit, ...)`
      - The printf function provided by the system. May not be available on all platforms.

    * - :code:`puts(x: strlit)`
      - Prints to the standard output

    * - :code:`sleep(seconds: i32)`
      - System sleep in seconds

    * - :code:`usleep(microsec: i32)`
      - System sleep in microseconds

    * - :code:`exit(code: i32)`
      - exits the application early. :code:`exit(1)` is used for an early exit in case of an exception at runtime.

.. note::

  These are all available in the :code:`math` module

TO BE COMPLETED

.. list-table:: math functions
    :widths: 50,80
    :header-rows: 1

    * - function
      - description

    * -
      -