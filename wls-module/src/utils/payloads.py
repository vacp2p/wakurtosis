# Python Imports
import random
import base64

# Project Imports
from src.utils import wls_logger
from src.utils import rtnorm


def _make_hex_payload(bytes_size):
    # Multiplied by 4 because each character in a string is one byte, so in a hex
    # we cannot go to two characters, this means we can only use 4 bits per byte.
    # We send half of the information but with the correct size, and as this is for testing purposes
    # we don't care about the information we are sending.
    if bytes_size == 0:
        raise ValueError('Payload size cannot be 0')

    payload = hex(random.getrandbits(4 * bytes_size))

    wls_logger.G_LOGGER.debug(f"Payload of size {bytes_size} bytes: {payload}")
    return payload


def _make_base64_payload(bytes_size):
    # Note this is effective payload, it does not match with base64EncodedSize
    if bytes_size == 0:
        raise ValueError('Payload size cannot be 0')

    random_bytes = bytes(random.choices(range(256), k=bytes_size))
    base64_bytes = base64.b64encode(random_bytes)
    base64_string = base64_bytes.decode('utf-8')

    return base64_string


def _make_uniform_dist(min_size, max_size):
    size = int(random.uniform(min_size, max_size))

    # Reject non even sizes
    while (size % 2) != 0:
        size = int(random.uniform(min_size, max_size))

    return _make_base64_payload(size), size


def _make_gaussian_dist(min_size, max_size):
    σ = (max_size - min_size) / 5.
    μ = (max_size - min_size) / 2.
    size = int(rtnorm.rtnorm(min_size, max_size, sigma=σ, mu=μ, size=1))

    # Reject non even sizes
    while (size % 2) != 0:
        size = int(rtnorm.rtnorm(min_size, max_size, sigma=σ, mu=μ, size=1))

    return _make_base64_payload(size), size


def make_payload_dist(dist_type, min_size, max_size):
    # Check if min and max packet sizes are the same
    if min_size == max_size:
        wls_logger.G_LOGGER.warning(f"Packet size is constant: min_size=max_size={min_size}")
        return _make_base64_payload(min_size), min_size

    # Payload sizes are even integers uniformly distributed in [min_size, max_size]
    if dist_type == 'uniform':
        return _make_uniform_dist(min_size, max_size)

    # Payload sizes are even integers ~"normally" distributed in [min_size, max_size]
    if dist_type == 'gaussian':
        return _make_gaussian_dist(min_size, max_size)

    wls_logger.G_LOGGER.error(f"Unknown distribution type {dist_type}")

    raise ValueError('Unknown distribution type %s' % dist_type)
