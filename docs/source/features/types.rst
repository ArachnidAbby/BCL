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
      - 1b (most CPUs cannot work with single bits)
    * -
      - char
      - 1B, 8b
    
    * -
      - 
      - 

    * - ints
      - i8
      - 1B
    * - ints
      - i16
      - 2B, 16b
    * - ints
      - i32
      - 4B, 32b
    * - ints
      - i64
      - 8B, 64b
      
    * -
      - 
      - 
    
    * - floats
      - f32
      - 4B
    * - floats
      - f64
      - 8B