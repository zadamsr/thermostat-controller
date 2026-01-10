import unittest

def add(a, b):
    return a + b

class TestPythonWorking(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(add(2, 2), 4)

if __name__ == "__main__":
    unittest.main()