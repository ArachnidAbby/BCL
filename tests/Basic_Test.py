import os
import sys
import unittest

p = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{p}/../src')

import compile
import errors

errors.SILENT_MODE = True

class basictests(unittest.TestCase):
    def test_functions(self):
        test_code = """
        define main() { 
            println 2;
            println(test_func(2, 10)); 
            2.test_func(10);
            (2, 10).test_func();
        }
        define test_func(x: i32, y: i32) -> i32 { return x+y;}
        """

        compile.compile_silent(test_code, f'{p}/random/test_functions.ll')

    def test_function_overloading(self):
        test_code = """
        define main() { 
            println 2;
            println(test_func(2, 10)); 
            2.test_func(10);
            (2, 10).test_func();

            0.2.test_func(0.8);
        }
        define test_func(x: i32, y: i32) -> i32 { return x+y;}
        define test_func(x: f64, y: f64) -> f64 { return x+y;}
        """

        compile.compile_silent(test_code, f'{p}/random/test_functions_2.ll')
    
    @unittest.expectedFailure
    def test_variables_1(self):
        test_code = """
        define main() { 
            println(test);
            test = 10;
        }
        """

        compile.compile_silent(test_code, f'{p}/random/test_variables_1.ll')
    
    @unittest.expectedFailure
    def test_variables_2(self):
        test_code = """
        define main() { 
            {
                x = 22;
            }
            x = x+4;
        }
        """

        compile.compile_silent(test_code, f'{p}/random/test_variables_2.ll')
    
    def test_variables_3(self):
        test_code = """
        define main() { 
            x = 22;
            {
                x = x+4;
            }
        }
        """

        compile.compile_silent(test_code, f'{p}/random/test_variables_3.ll')

    def test_ops(self):
        test_code = """
        define main() { 
            8+2*8-292/15==9;
            not true;
            true and true;
            true and not true;
            true or true and not true;
        }
        """

        compile.compile_silent(test_code, f'{p}/random/test_ops.ll')


if __name__ == '__main__':
    unittest.main()
