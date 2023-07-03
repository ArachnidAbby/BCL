import os
import sys
import unittest
from pathlib import Path

p = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{p}/../src')

import compile  # NOQA: E402
import errors  # NOQA: E402

errors.SILENT_MODE = True


class basictests(unittest.TestCase):
    def test_creation(self):
        test_code = """
        import stdlib::*;

        define main() {
            x = [true; 200];
            y = [[true; 200]; 200];
        }
        """

        file = Path(f'{p}/random/arrays/test_creation.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)

    def test_indexing(self):
        test_code = """
        import stdlib::*;

        define main() {
            x = [true; 200];
            y = [[true; 200]; 200];
            println(x[19]);
            println(y[12][13]);
        }
        """

        file = Path(f'{p}/random/arrays/test_index.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)

    @unittest.expectedFailure
    def test_over_indexing(self):
        test_code = """
        import stdlib::*;

        define main() {
            x = [true; 200];
            y = [[true; 200]; 200];
            println(x[19]);
            println(y[12][200]); // over index
        }
        """

        file = Path(f'{p}/random/arrays/test_over_index.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)

    def test_functions(self):
        test_code = """
        import stdlib::*;

        define main() {
            x = [true; 200];
            y = [[true; 200]; 200];
            println(x[19]);
            println(y[12][13]);
            println(array_function(x, 12));
        }

        define array_function(array: bool[200], n: i32) -> bool {
            return array[n];
        }
        """

        file = Path(f'{p}/random/arrays/test_functions.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)

    def test_index_assign(self):
        test_code = """
        import stdlib::*;

        define main() {
            x = [true; 200];
            x[12] = false;
            println(x[12]);
        }
        """

        file = Path(f'{p}/random/arrays/test_index_assign.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)

    def test_math(self):
        test_code = """
        import stdlib::*;

        define main() {
            x = [true; 200];
            y: i32 = 29 + x[12] * x[89];
            println(y); // should print 30
        }
        """

        file = Path(f'{p}/random/arrays/test_math.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)

    def test_index_with_vars(self):
        test_code = """
        import stdlib::*;

        define main() {
            x = [true; 200];
            y = 125;
            println(x[y]); // should print 30
        }
        """

        file = Path(f'{p}/random/arrays/test_index_w_vars.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)

    def test_assign_with_vars(self):
        test_code = """
        import stdlib::*;

        define main() {
            x = [true; 200];
            y = 125;
            x[y] = false;
            println(x[y]); // should print 30
        }
        """

        file = Path(f'{p}/random/arrays/test_assign_w_vars.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)

    def test_arrays_of_structs(self):
        test_code = """
        import stdlib::*;

        struct struct_for_array {
            x: bool,
            y: bool;
        }

        define main() {
            x = [struct_for_array {x: true, y: false}; 200];
            println(x[12].y);
            struct_array_printer(x);
        }

        define struct_array_printer(input: struct_for_array[200]) {
            for c in 0..200 {
                print("item: ");
                println(c);
                print("  x: ");
                println(input[c].x);
                print("  y: ");
                println(input[c].y);
            }
        }
        """

        file = Path(f'{p}/random/arrays/test_struct_arrays.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)

    def test_inplace_ops(self):
        test_code = """
        import stdlib::*;

        define main() {
            x = [0; 200];
            x[12] += 22;
            x[12] -= 2;
            x[12] *= 2;
            x[12] /= 2;
            println(x[12]);
        }
        """

        file = Path(f'{p}/random/arrays/test_inplace_ops.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)


if __name__ == '__main__':
    unittest.main()
