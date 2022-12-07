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

        compile.compile(test_code, f'{p}/random/test_functions.ll')

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
        define test_func(x: f32, y: f32) -> f32 { return x+y;}
        """

        compile.compile(test_code, f'{p}/random/test_functions_2.ll')
    
    @unittest.expectedFailure
    def test_variables_1(self):
        test_code = """
        define main() { 
            println(test);
            test = 10;
        }
        """

        compile.compile(test_code, f'{p}/random/test_variables_1.ll')
    
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

        compile.compile(test_code, f'{p}/random/test_variables_2.ll')
    
    def test_variables_3(self):
        test_code = """
        define main() { 
            x = 22;
            {
                x = x+4;
            }
        }
        """

        compile.compile(test_code, f'{p}/random/test_variables_3.ll')

    def test_ops(self):
        test_code = """
        define main() { 
            8+2*8-292/15==9;
            12 * test(15);
            not true;
            true and true;
            true and not true;
            true or true and not true;
        }

        define test(x: i32) -> i32 { return 12;}
        """

        compile.compile(test_code, f'{p}/random/test_ops.ll')
    
    def test_if_else_if(self):
        test_code = """
        define main() { 
            if true {
                println(9);
            }

            if true {
                println(0);
            }else {
                println(9);
            }
        }
        """

        compile.compile(test_code, f'{p}/random/test_ifs.ll')
    
    def test_arrays(self):
        test_code = """
        define main() { 
            x = 6;
            test = [0,0,0,0];
            jest = [[1,2], [3,4]];

            println(jest[0][0]);
            jest[0][0] = 9;
            println(jest[0][0]);
            println(test[x]);
            test[x] = 8;
            println(test[x]);
        }
        """

        compile.compile(test_code, f'{p}/random/test_arrays.ll')

    def test_arrays_index_literals(self):
        test_code = """
        define main() { 
            println([true; 12][10]);
            println(test()[2]);
        }

        define test() -> i32[5] {
            return [12; 5];
        }
        """

        compile.compile(test_code, f'{p}/random/test_arrays_indLit.ll')

    def test_arrays_index_math(self):
        test_code = """
        define main() {
            x = [1, 2, 4, 8, 16];
            println(x[0]+x[2]);
        }

        define test() -> i32[5] {
            return [12; 5];
        }
        """

        compile.compile(test_code, f'{p}/random/test_arrays_indmath.ll')

    @unittest.expectedFailure
    def test_array_fail(self):
        test_code = """
        define main() { 
            test = [0,0,0];
            test[4]; // over-index
        }
        """

        compile.compile(test_code, f'{p}/random/test_array_fail.ll')


if __name__ == '__main__':
    unittest.main()
