Imports
========

Imports allow you to bring in other modules.

Currently these are added directly into the global namespace.


.. note::

    Later imports will not automatically be in the global namspace.

####################
How to do an import
####################

.. tip::

    You should always import :code:`stdlib`! Especially if you need to work with arrays!

.. code-block:: bcl

    import my_module;

    define main() {
        // this function isn't defined here, we imported it
        function_from_my_module();
    }
