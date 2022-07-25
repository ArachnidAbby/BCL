Types
======

This guide goes over types.

---------------
primitive types
---------------

BCL has your standard primitive types that directly correlate to llvm types.

.. list-table:: primitive types
    :widths: 20 30 30
    :header-rows: 1

    * - family (if applies)
      - type
      - size

    * -
      - boolean
      - 1B, 8b (Cpu can't work with smaller than a byte)
    * -
      - char
      - 1B
    
    * -
      - 
      - 

    * - ints
      - byte
      - 1B
    * - ints
      - short
      - 2B, 16b
    * - ints
      - int
      - 4B, 32b
    * - ints
      - long
      - 8B, 64b
      
    * -
      - 
      - 
    
    * - floats
      - float
      - 4B
    * - floats
      - double
      - 8B