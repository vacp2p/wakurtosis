# Python Imports
import random

# Project Imports
from . import wls_logger
from . import rtnorm


def _make_payload(bytes_size):
    # todo preguntar: cuando enviamos un payload, se tiene en cuenta el 0x en el tamaño?
    # todo por que coño se multiplica por 4, si el tamaño es en bytes?
    # Si multiplicamos por 4, tenemos 4 bits, que es medio byte, 1 hexadecimal, deberian ser 2.
    payload = hex(random.getrandbits(4 * bytes_size))
    # payload = hex(random.getrandbits(8 * bytes_size))
    wls_logger.G_LOGGER.debug(f"Payload of size {bytes_size} bytes: {payload}")
    return payload


def _make_uniform_dist(min_size, max_size):
    size = int(random.uniform(min_size, max_size))

    # Reject non even sizes
    while (size % 2) != 0:
        size = int(random.uniform(min_size, max_size))

    return _make_payload(size), size


def _make_gaussian_dist(min_size, max_size):
    σ = (max_size - min_size) / 5.
    μ = (max_size - min_size) / 2.
    size = int(rtnorm.rtnorm(min_size, max_size, sigma=σ, mu=μ, size=1))

    # Reject non even sizes
    while (size % 2) != 0:
        size = int(rtnorm.rtnorm(min_size, max_size, sigma=σ, mu=μ, size=1))

    return _make_payload(size), size


def make_payload_dist(dist_type, min_size, max_size):
    # Check if min and max packet sizes are the same
    if min_size == max_size:
        wls_logger.G_LOGGER.warning(f"Packet size is constant: min_size=max_size={min_size}")
        return _make_payload(min_size), min_size

    # Payload sizes are even integers uniformly distributed in [min_size, max_size]
    if dist_type == 'uniform':
        return _make_uniform_dist(min_size, max_size)

    # Payload sizes are even integers ~"normally" distributed in [min_size, max_size]
    if dist_type == 'gaussian':
        return _make_gaussian_dist(min_size, max_size)

    wls_logger.G_LOGGER.error(f"Unknown distribution type {dist_type}")

    raise ValueError('Unknown distribution type %s' % dist_type)
