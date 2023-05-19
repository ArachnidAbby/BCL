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
    def test_definition(self):
        test_code = """
        import stdlib;

        struct TestStruct {
            x: f32,
            y: i32;
        }
        """

        file = Path(f'{p}/random/structs/test_definition.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)

    def test_nested_definition(self):
        test_code = """
        import stdlib;

        // nesting, but Container is above the definition of TestStruct
        struct Container {
            x: TestStruct;
        }

        struct TestStruct {
            x: f32,
            y: i32;
        }
        """

        file = Path(f'{p}/random/structs/test_nested_definition.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)

    def test_instantiation(self):
        test_code = """
        import stdlib;

        struct TestStruct {
            x: f32,
            y: i32;
        }

        define main() {
            var = TestStruct {x: 15f, y: 12};
        }
        """

        file = Path(f'{p}/random/structs/test_instantiation.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)

    def test_nested_instantiation(self):
        test_code = """
        import stdlib;

        struct Container {
            x: TestStruct;
        }

        struct TestStruct {
            x: f32,
            y: i32;
        }

        define main() {
            var = Container {x: TestStruct {x: 15f, y: 12}};
        }
        """

        file = Path(f'{p}/random/structs/test_nested_instantiation.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)

    def test_member_access(self):
        test_code = """
        import stdlib;

        struct TestStruct {
            x: f32,
            y: i32;
        }

        define main() {
            var = TestStruct {x: 15f, y: 12};
            println(var.x);
            var.x += 12f;
            println(var.x);
        }
        """

        file = Path(f'{p}/random/structs/test_member_access.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)

    def test_methods(self):
        test_code = """
        import stdlib;

        struct TestStruct {
            x: f32,
            y: i32;

            define set_x(&self, x: f32){
                self.x = x;
            }

            define println(self) {
                println(self.x);
            }
        }

        define main() {
            var = TestStruct {x: 15f, y: 12};
            var.println();
            var.set_x(12f);
            var.println();
        }
        """

        file = Path(f'{p}/random/structs/test_methods.ll')
        compile.compile(test_code, file,
                        compile.DEFAULT_ARGS)


if __name__ == '__main__':
    unittest.main()
