import unittest

from test import tests


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(tests)
