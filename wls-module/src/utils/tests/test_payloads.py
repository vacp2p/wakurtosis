import unittest
import random
from unittest.mock import patch

from src.utils import payloads

random.seed(1)


class TestPayloads(unittest.TestCase):

    def create_patch(self, name):
        patcher = patch(name)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def test__make_payload(self):
        payload = payloads._make_payload(1)
        print(payload)
        print(b"a")
        self.assertEqual(payload, '0x9')

    def test__make_payload_error(self):
        with self.assertRaises(ValueError):
            payloads._make_payload(0)

    def test__make_uniform_dist(self):
        payload, size = payloads._make_uniform_dist(1, 10)
        self.assertEqual(payload, '0xc386bbc4')
        self.assertEqual(size, 8)

    def test__make_gaussian_dist(self):
        mock_rtnorm = self.create_patch('src.utils.rtnorm.rtnorm')
        mock_rtnorm.return_value = 6

        payload, size = payloads._make_gaussian_dist(1, 10)
        self.assertEqual(payload, '0x2265b1')
        self.assertEqual(size, 6)

    def test_make_payload_dist_same(self):
        payload, size = payloads.make_payload_dist('test', 1, 1)
        self.assertEqual(payload, '0x1')
        self.assertEqual(size, 1)

    def test_make_payload_dist_uniform(self):
        payload, size = payloads.make_payload_dist('uniform', 1, 10)
        self.assertEqual(payload, '0xc9e9c6')
        self.assertEqual(size, 6)

    def test_make_payload_dist_gaussian(self):
        mock__make_gaussian_dist = self.create_patch('src.utils.payloads._make_gaussian_dist')
        mock__make_gaussian_dist.return_value = '0x213', 3

        payload, size = payloads.make_payload_dist('gaussian', 1, 10)
        self.assertEqual(payload, '0x213')
        self.assertEqual(size, 3)

    def test_make_payload_dist_error(self):
        with self.assertRaises(ValueError):
            payloads.make_payload_dist('test', 1, 4)
