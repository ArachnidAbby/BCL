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
        files = os.listdir("tests/file_tests")
        for file in files:
            print(file)
            last = file
            output = compile_file(f"tests/file_tests/{file}")
            assert output == 0, f"successful: {succeeded}\n\nlast: {last}"
            succeeded.append(file)


if __name__ == '__main__':
    unittest.main()
