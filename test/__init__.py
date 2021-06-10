import unittest

from .models import TestDBModels
from .core import TestAppCore
from .api import TestHTTPAPI


tests = unittest.TestSuite()
tests.addTest(unittest.makeSuite(TestDBModels))
tests.addTest(unittest.makeSuite(TestAppCore))
tests.addTest(unittest.makeSuite(TestHTTPAPI))
