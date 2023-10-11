import os
import sys
import unittest
from pathlib import Path

p = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{p}/../src')
succeeded = []
last = None


def compile_file(dir):
    # Have to do it this way due to llvm goofyness
    return os.system(f"env/bin/python {p}/../src/main.py compile {dir} --emit-binary")


class AllTest(unittest.TestCase):

    def test_all(self):
        global last
        print("\n")

        files = os.listdir("tests/file_tests")
        for file in files:
            print(file, end="", flush=True)
            last = file
            output = compile_file(f"tests/file_tests/{file}")
            should_fail = file.endswith(".should_fail.bcl") * 1
            if output != 0 and not should_fail:
                print(": F")

            assert (output == 0) ^ should_fail, \
                   f"\nsuccessful: {len(succeeded)}\n\nlast: {last}"
            succeeded.append(file)
            print(": P" + ("(F)" * should_fail))

        print(f"\n\nFinished {len(files)} tests\n")


if __name__ == '__main__':
    unittest.main()
