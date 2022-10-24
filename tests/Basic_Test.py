import os
import sys
import unittest

p = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{p}/../src')

import Compile
import Errors

Errors.SILENT_MODE = True

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

        Compile.compile_silent(test_code, f'{p}/random/test_functions.ll')

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

        Compile.compile_silent(test_code, f'{p}/random/test_functions.ll')
    
    @unittest.expectedFailure
    def test_variables_1(self):
        test_code = """
        define main() { 
            println(test);
            test = 10;
        }
        """

        Compile.compile_silent(test_code, f'{p}/random/test_variables_1.ll')
    
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

        Compile.compile_silent(test_code, f'{p}/random/test_variables_2.ll')
    
    def test_variables_3(self):
        test_code = """
        define main() { 
            x = 22;
            {
                x = x+4;
            }
        }
        """

        Compile.compile_silent(test_code, f'{p}/random/test_variables_3.ll')

if __name__ == '__main__':
    unittest.main()
