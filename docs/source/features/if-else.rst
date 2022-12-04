if, else, and else if
======================

---
if
---

.. code-block:: bcl

    define main() {
        if 0 >= -1 {
            println("true");
        }
    }


-----
else
-----

.. code-block:: bcl

    define main() {
        if 0 == -1 {
            println("true");
        } else {
            println("not true");
        }
    }

--------
else if
--------

.. code-block:: bcl

    define main() {
        if 0 == -1 {
            println("true");
        } else if 8==0{
            println("elif true");
        } else {
            println("not true");
        }
    }