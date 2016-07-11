from cachetools.cache import Cache
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


class AggressiveLFUCache(Cache):
    """Aggressive Least Frequently Used (LFU) cache implementation."""

    def __init__(self, maxsize, missing=missing, getsizeof=None):
        super(AggressiveLFUCache, self).__init__(maxsize, missing, getsizeof)
        self.__counter = collections.Counter()
        self.__cache_misses = 0

    def __getitem__(self, key, cache_getitem=Cache.__getitem__):
        self.__counter[key] -= 1
        if key not in self:
            self.__cache_misses += 1
        value = cache_getitem(self, key)
        return value

    def __setitem__(self, key, value, cache_setitem=Cache.__setitem__):
        size = self.getsizeof(value)
        if self.maxsize > 0:
            if self.currsize == 0:
                cache_setitem(self, key, value)

            elif self.currsize > 0:
                # freqs = sorted([(k, self.__counter[k]) for k in self.keys()], key=lambda x: x[1], reverse=True)
                # lfkey, lfcount = freqs[0]
                # if (lfcount > self.__counter[key]) or (lfcount*0.8 < self.__counter[key]):

                cache_setitem(self, key, value)
                # calculate frequency of cache items
                freqs = sorted([(k, self.__counter[k]) for k in self.keys()], key=lambda x: x[1], reverse=True)
                # clean up the cache
                for n in range(len(freqs) - 1):
                    lfkey1, lfcount1 = freqs[n]
                    lfkey2, lfcount2 = freqs[n + 1]
                    if lfcount1 <= lfcount2:
                        self.pop(lfkey1)
                        self.__counter[lfkey1] += 1



    def __delitem__(self, key, cache_delitem=Cache.__delitem__):
        cache_delitem(self, key)

    def __repr__(self):
        return Cache.__repr__(self) + "\n" + str(self.__counter)

    def getcounter(self):
        return self.__counter

    def getmisses(self):
        return self.__cache_misses

    def getleastratio(self):
        freqs = sorted([(k, self.__counter[k]) for k in self.keys()], key=lambda x: x[1], reverse=True)
        return float(freqs[1][1])/freqs[0][1]


if __name__ == '__main__':
    import numpy as np
    from scipy.stats import zipf
    cache = AggressiveLFUCache(200)
    num = 200
    z = ZipfGenerator(num, 0.8)
    # queries = zipf.pmf(range(1, num), 1.1)
    # print queries
    queries = []
    for n in range(num):
        q = z.next()
        v = cache[q]
        print cache
        queries.append(q)
    print("Misses:{}".format(cache.getmisses()))
    # counter = collections.Counter(queries)
    # print counter
    # labels, values = zip(*counter.items())
    # plt.loglog(labels, values)
    # plt.show()
