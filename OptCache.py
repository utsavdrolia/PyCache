import collections

import numpy
import scipy
from matplotlib import pyplot as plt
from scipy.stats import skew
from scipy.stats import kurtosis

from ZipfGenerator import ZipfGenerator
from pulp import *


def missing(key):
    return key


class OptCache(dict):
    """ILP based cache implementation that uses frequency to predict future and optimize cache allocation """

    def __init__(self, N=5000, priors=None, **kwargs):
        super(OptCache, self).__init__(**kwargs)
        self.__counter = collections.Counter()
        self.__interval = 1000
        self.__prev_opt = 0
        self.__interval_multiplier = 1
        self.__cache_misses = 0
        self.__currsize = 0
        self.__reqcounter = 0

        self.N = N
        cloudcomput_const = 1  # 400 images in 400ms
        network_latency = 70  # ms
        network_bw = 5.0 / 8  # MBps
        request_size = 50.0 / 1000  # MB per image
        nw_lat = network_latency + (request_size / network_bw) * 1000

        self.L = nw_lat + cloudcomput_const * self.N
        self.l = 2.0  # 2ms/object

        # Dirichlet prior
        # If no prior specified, start from scratch:
        if priors is None:
            # alpha = 1.0/N
            alpha = max(0.0005*N, 1)
            # alpha = 0.1
            # alpha = 100
            # alpha = max(0.001*N,1)
            # alpha = N
            for n in range(N):
                self.__counter[n] += alpha
        else:
            self.__counter = collections.Counter(priors)
            max_val = max(self.__counter.values())
            # scale the previous counter values such that max is hundred
            for k in self.__counter.keys():
                self.__counter[k] = int(((self.__counter[k]/max_val) * 100)) + 1

        self.__reqcounter += sum(self.__counter.values())
        self.__x_vars = LpVariable.dicts("x", self.__counter.keys(), 0, 1, cat='Integer')

    def __getitem__(self, key):
        # Increase requests for key
        self.__counter[key] += 1
        self.__reqcounter += 1
        # CHeck if in cache
        if key not in self:
            # If not get from missing and BUT DO NOT insert
            self.__cache_misses += 1
            value = missing(key)
        else:
            value = super(OptCache, self).__getitem__(key)

        # Check if interval reached
        count = self.__reqcounter
        if (count - self.__prev_opt) >= (self.__interval*self.__interval_multiplier):
            self.optimize_cache()
            self.__prev_opt = count
            if self.__interval_multiplier != 1:
                self.__interval_multiplier -= 1

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
        x_vars = self.__x_vars
        print ("Total requests:{}".format(self.__reqcounter))
        prob = LpProblem(name="Cache", sense=LpMinimize)
        costfunction = self.create_cost_fx(x_vars)
        prob.setObjective(costfunction)
        prob.solve()
        self.allocate_cache(x_vars)
        print ("Cache Size:{}".format(len(self)))
        print("Status:{}".format(prob.status))
        print("Solution time:{}".format(prob.solutionTime))

    def allocate_cache(self, x_vars):
        for key in self.__counter.keys():
            if value(x_vars[key]) == 1 and key not in self:
                super(OptCache, self).__setitem__(key, missing(key))
            elif value(x_vars[key]) == 0 and key in self:
                super(OptCache, self).__delitem__(key)

    def create_cost_fx(self, x_vars):
        exps = []

        # sigma(x_i(l-L*p_i) + L*p_i)
        for key in self.__counter.keys():
            p_i = float(self.__counter[key]) / self.__reqcounter
            Lp_i = self.L * p_i
            exps.append(LpAffineExpression(e=[(x_vars[key], self.l - Lp_i)], constant=Lp_i))
        costfunction = lpSum(exps)
        return costfunction

    def getmaxsize(self):
        return int(self.L/self.l)


if __name__ == '__main__':
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
