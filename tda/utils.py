import re
from collections import OrderedDict
from io import TextIOWrapper
from typing import Generic, Hashable, Optional, TypeVar
from log_structure import LogCluster

patterns = [
    r'(\d+[\.-])+\d+',  # time. eg, 2005-06-14-09.11.51.127157
    # TODO hex
]





def read_line(file_path: str) -> list:
    # TODO a better iterator that is friendly with memory
    lines = []
    with open(file_path) as file:
        for line in file:
            lines.append(line)
    return lines


def gen_header(log_format: str):
    compiled = re.compile(r'<\w+>')
    headers = compiled.findall(log_format)
    headers = [header.strip('<').strip('>') for header in headers]
    return headers

    # compiled = re.compile(r'\W')
    # tokens = compiled.split(line)
    # tokens = filter(lambda s: s and s.strip(), tokens) # get rid of empty elements
    # return list(tokens)


def plot_cdf(data, cdfs, tps):
    import numpy as np
    import matplotlib.pyplot as plt
    data = np.array(data)
    x = np.arange(0, len(data))
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)
    ax1.scatter(x, data, label='origin', s=5)
    ax2.scatter(x, cdfs, label='cdf', s=5)
    ax3.scatter(x, tps, label='tp', s=5)
    plt.show()


T = TypeVar("T")


class LruCache(Generic[T]):
    """
    refer to: https://jellis18.github.io/post/2021-11-25-lru-cache/
    """

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.__cache: OrderedDict[LogCluster, int] = OrderedDict()
        self.value = 0

    def __get(self, key: LogCluster) -> Optional[T]:
        if key not in self.__cache:
            return None
        self.__cache.move_to_end(key)
        return self.__cache[key]

    def insert(self, key: LogCluster) -> None:

        if len(self.__cache) >= self.capacity:
            template, log_cluster = self.__cache.popitem(last=False)
            # TODO: consider if this log cluster should be removed from trie
            # parent = log_cluster.parent
            # assert parent is not None and parent.isEnd
            # parent.remove_log_cluster(log_cluster)

        self.__cache[key] = self.value
        self.__cache.move_to_end(key)

    def get_cache(self) -> list[LogCluster]:
        """
        get cached log clusters if there is no feedback
        """
        return list(self.__cache)

    def clear(self) -> None:
        self.__cache.clear()

    def __len__(self) -> int:
        return len(self.__cache)

    def __iter__(self):
        # refer to: https://blog.csdn.net/qq_51352578/article/details/125507312
        return self.__cache.__iter__()

    def __getitem__(self, item):
        return self.__get(item)
