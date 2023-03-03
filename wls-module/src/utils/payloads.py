# Python Imports
import random

# Project Imports
import logger
import rtnorm

G_LOGGER, handler = logger.innit_logging()


def _make_payload(size):
    payload = hex(random.getrandbits(4 * size))
    G_LOGGER.debug('Payload of size %d bytes: %s' % (size, payload))
    return payload


def make_payload_dist(dist_type, min_size, max_size):
    # Check if min and max packet sizes are the same
    if min_size == max_size:
        G_LOGGER.warning('Packet size is constant: min_size=max_size=%d' % min_size)
        return _make_payload(min_size), min_size

    # Payload sizes are even integers uniformly distributed in [min_size, max_size]
    if dist_type == 'uniform':
        size = int(random.uniform(min_size, max_size))

        # Reject non even sizes
        while (size % 2) != 0:
            size = int(random.uniform(min_size, max_size))

        return _make_payload(size), size

    # Payload sizes are even integers ~"normally" distributed in [min_size, max_size]
    if dist_type == 'gaussian':
        σ = (max_size - min_size) / 5.
        μ = (max_size - min_size) / 2.
        size = int(rtnorm.rtnorm(min_size, max_size, sigma=σ, mu=μ, size=1))

        # Reject non even sizes
        while (size % 2) != 0:
            size = int(rtnorm.rtnorm(min_size, max_size, sigma=σ, mu=μ, size=1))

        return _make_payload(size), size

    G_LOGGER.error('Unknown distribution type %s')

    return '0x00', 0
