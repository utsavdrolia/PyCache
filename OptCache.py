import collections

from matplotlib import pyplot as plt

from ZipfGenerator import ZipfGenerator
from pulp import *


def missing(key):
    return key
#
# def popitem(self):
#     """Remove and return the `(key, value)` pair least frequently used."""
#     try:
#         (key, _), = self.__counter.most_common(1)
#     except ValueError:
#         raise KeyError('%s is empty' % self.__class__.__name__)
#     else:
#         return (key, self.pop(key))


class OptCache(dict):
    """ILP based cache implementation that uses frequency to predict future and optimize cache allocation """

    def __init__(self, interval, **kwargs):
        super(OptCache, self).__init__(**kwargs)
        self.__counter = collections.Counter()
        self.__interval = interval
        self.__interval_counter = 5
        self.__cache_misses = 0
        self.__currsize = 0

        N = 500
        cloudcomput_const = 1  # 400 images in 400ms
        network_latency = 70  # ms
        network_bw = 5.0 / 8  # MBps
        request_size = 50.0 / 1000  # MB per image
        nw_lat = network_latency + (request_size / network_bw) * 1000

        self.L = nw_lat + cloudcomput_const * N
        self.l = 2.0  # 2ms/object

    def __getitem__(self, key):
        # Increase requests for key
        self.__counter[key] += 1

        # CHeck if in cache
        if key not in self:
            # If not get from missing and BUT DO NOT insert
            self.__cache_misses += 1
            value = missing(key)
        else:
            value = super(OptCache, self).__getitem__(key)

        # Check if interval reached
        if sum(self.__counter.values()) % self.__interval == 0:
            self.optimize_cache()
        # if sum(self.__counter.values()) % (self.__interval * self.__interval_counter) == 0:
        #     self.optimize_cache()
            # if self.__interval_counter != 1:
            #     self.__interval_counter -= 1

        return value

    def __repr__(self):
        return super(OptCache, self).__repr__() + "\n" + str(self.__counter)

    def getcounter(self):
        return self.__counter

    def getmisses(self):
        return self.__cache_misses

    def getleastratio(self):
        freqs = sorted([(k, self.__counter[k]) for k in self.keys()], key=lambda x: x[1], reverse=True)
        return float(freqs[1][1])/freqs[0][1]

    def optimize_cache(self):
        print ("Total requests:{}".format(sum(self.__counter.values())))
        prob = LpProblem(name="Cache", sense=LpMinimize)
        x_vars = LpVariable.dicts("x", self.__counter.keys(), 0, 1, cat='Integer')
        costfunction = self.create_cost_fx(x_vars)
        prob.setObjective(costfunction)
        prob.solve()
        print("Status:", LpStatus[prob.status])
        for key in self.__counter.keys():
            if value(x_vars[key]) == 1 and key not in self:
                super(OptCache, self).__setitem__(key, missing(key))
            elif value(x_vars[key]) == 0 and key in self:
                super(OptCache, self).__delitem__(key)

        print ("Cache Size:{}".format(len(self)))

    def create_cost_fx(self, x_vars):
        exps = []
        # sigma(x_i(l-L*p_i) + L*p_i)
        for key in self.__counter.keys():
            p_i = float(self.__counter[key]) / sum(self.__counter.values())
            Lp_i = self.L * p_i
            exps.append(LpAffineExpression(e=[(x_vars[key], self.l - Lp_i)], constant=Lp_i))
        costfunction = lpSum(exps)
        return costfunction


if __name__ == '__main__':
    import numpy as np
    from scipy.stats import zipf
    cache = OptCache(100)
    num = 10000
    z = ZipfGenerator(300, 0.8)
    # queries = zipf.pmf(range(1, num), 1.1)
    # print queries
    queries = []
    for n in range(num):
        q = z.next()
        v = cache[q]
    print("Misses:{}".format(cache.getmisses()))
    # counter = collections.Counter(queries)
    # print counter
    # labels, values = zip(*counter.items())
    # plt.loglog(labels, values)
    # plt.show()
