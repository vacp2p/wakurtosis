import unittest
import random

from src.utils import payloads

random.seed(1)


class TestPayloads(unittest.TestCase):

    """
    def test__make_payload(self):
        payload = payloads._make_payload(1)
        print(payload)
        print(b"a")
        self.assertEqual(payload, '0x2')


    def test__make_payload_error(self):
        with self.assertRaises(ValueError):
            payloads._make_payload(0) <<- todo añadir error
    """

    def test__make_uniform_dist(self):
        payload, size = payloads._make_uniform_dist(1, 10)
        self.assertEqual(payload, '0xd8')
        self.assertEqual(size, 2)

    # def test__make_uniform_dist_error(self): <<- todo

    """
    def test__make_gaussian_dist(self):
        payload, size = payloads._make_gaussian_dist(1, 10) <<- path as it does not use random
        self.assertEqual(payload, '0x2265')
        self.assertEqual(size, 2)
    """

    def test_make_payload_dist_same(self):
        payload, size = payloads.make_payload_dist('test', 1, 1)
        self.assertEqual(payload, '0xd8')
        self.assertEqual(size, 2)

    def test_make_payload_dist_uniform(self):
        payload, size = payloads.make_payload_dist('uniform', 1, 10)
        self.assertEqual(payload, '0xcd')
        self.assertEqual(size, 2)

    """
    def test_make_payload_dist_gaussian(self):
        payload, size = payloads.make_payload_dist('gaussian', 1, 3) <<- same as test before
        self.assertEqual(payload, '0x2265')
        self.assertEqual(size, 2)
    """

    def test_make_payload_dist_error(self):
        with self.assertRaises(ValueError):
            payloads.make_payload_dist('test', 1, 4)
