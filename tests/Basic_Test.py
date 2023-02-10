import os
import sys
import unittest

p = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{p}/../src')

import compile  # NOQA: E402
import errors  # NOQA: E402

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

        compile.compile(test_code, f'{p}/random/test_functions.ll',
                        compile.DEFAULT_ARGS)

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

        compile.compile(test_code, f'{p}/random/test_functions_2.ll',
                        compile.DEFAULT_ARGS)

    @unittest.expectedFailure
    def test_variables_1(self):
        test_code = """
        define main() {
            println(test);
            test = 10;
        }
        """

        compile.compile(test_code, f'{p}/random/test_variables_1.ll',
                        compile.DEFAULT_ARGS)

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

        compile.compile(test_code, f'{p}/random/test_variables_2.ll',
                        compile.DEFAULT_ARGS)

    def test_variables_3(self):
        test_code = """
        define main() {
            x = 22;
            {
                x = x+4;
            }
        }
        """

        compile.compile(test_code, f'{p}/random/test_variables_3.ll',
                        compile.DEFAULT_ARGS)

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

        compile.compile(test_code, f'{p}/random/test_ops.ll',
                        compile.DEFAULT_ARGS)

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

        compile.compile(test_code, f'{p}/random/test_ifs.ll',
                        compile.DEFAULT_ARGS)

    def test_named_constants(self):
        test_code = """
        define main() {
            radius = 12;
            println((radius*radius)*PI);
            println((radius*radius)*HALF_PI);
            println((radius*radius)*TWO_PI);
            println(true);
            println(false);
        }
        """

        compile.compile(test_code, f'{p}/random/test_named_consts.ll',
                        compile.DEFAULT_ARGS)

    def test_struct(self):
        test_code = """
        struct example {
            x: i32,
            y: i32;
        }

        define main() {
            j: example = example {x: 8, y: 2};
            println(j.x);
        }
        """

        compile.compile(test_code, f'{p}/random/test_struct_usage.ll',
                        compile.DEFAULT_ARGS)


if __name__ == '__main__':
    unittest.main()
