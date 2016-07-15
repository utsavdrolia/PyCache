import random
import bisect
import math

import numpy


class ZipfGenerator:

    def __init__(self, n, alpha):
        # Calculate Zeta values from 1 to n:
        tmp = [1. / (math.pow(float(i), alpha)) for i in range(1, n+1)]
        zeta = reduce(lambda sums, x: sums + [sums[-1] + x], tmp, [0])

        # Store the translation map:
        self.distMap = [x / zeta[-1] for x in zeta]

    def next(self):
        # Take a uniform 0-1 pseudo-random value:
        u = random.random()

        # Translate the Zipf variable:
        return bisect.bisect(self.distMap, u) - 1


def randZipf(n, alpha, numSamples):
    # Calculate Zeta values from 1 to n:
    tmp = numpy.power( numpy.arange(1, n+1), -alpha )
    zeta = numpy.r_[0.0, numpy.cumsum(tmp)]
    # Store the translation map:
    distMap = [x / zeta[-1] for x in zeta]
    # Generate an array of uniform 0-1 pseudo-random values:
    u = numpy.random.random(numSamples)
    # bisect them with distMap
    v = numpy.searchsorted(distMap, u)
    samples = [t-1 for t in v]
    return samples