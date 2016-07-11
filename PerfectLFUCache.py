import collections

from matplotlib import pyplot as plt

from ZipfGenerator import ZipfGenerator


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


class PerfectLFUCache(dict):
    """Perfect Least Frequently Used (LFU) cache implementation."""

    def __init__(self, maxsize, **kwargs):
        super(PerfectLFUCache, self).__init__(**kwargs)
        self.__counter = collections.Counter()
        self.__cache_misses = 0
        self.__maxsize = maxsize
        self.__currsize = 0

    def __getitem__(self, key):
        # Increase requests for key
        self.__counter[key] -= 1

        # CHeck if in cache
        if key not in self:
            # If not get from missing and try to insert
            self.__cache_misses += 1
            value = missing(key)
            self.__setitem__(key, value)
        else:
            value = super(PerfectLFUCache, self).__getitem__(key)
        return value

    def __setitem__(self, key, value):
        size = 1
        if self.__currsize + size > self.__maxsize:
            if self.__maxsize > 0:
                freqs = sorted([(k, self.__counter[k]) for k in self.keys()], key=lambda x: x[1], reverse=True)
                lfkey, lfcount = freqs[0]
                if lfcount > self.__counter[key]:
                    super(PerfectLFUCache, self).__delitem__(lfkey)
                    super(PerfectLFUCache, self).__setitem__(key, value)
        else:
            super(PerfectLFUCache, self).__setitem__(key, value)
            self.__currsize += 1

    def __repr__(self):
        return super(PerfectLFUCache, self).__repr__() + "\n" + str(self.__counter)

    def getcounter(self):
        return self.__counter

    def getmisses(self):
        return self.__cache_misses

    def getleastratio(self):
        freqs = sorted([(k, self.__counter[k]) for k in self.keys()], key=lambda x: x[1], reverse=True)
        return float(freqs[1][1])/freqs[0][1]

    def setmax(self, k):
        self.__maxsize = k

if __name__ == '__main__':
    import numpy as np
    from scipy.stats import zipf
    cache = PerfectLFUCache(20)
    num = 200
    z = ZipfGenerator(num, 0.8)
    # queries = zipf.pmf(range(1, num), 1.1)
    # print queries
    queries = []
    for n in range(num):
        q = z.next()
        v = cache[q]
        print q
        print cache
        queries.append(q)
    print("Misses:{}".format(cache.getmisses()))
    # counter = collections.Counter(queries)
    # print counter
    # labels, values = zip(*counter.items())
    # plt.loglog(labels, values)
    # plt.show()
