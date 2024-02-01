import re
from collections import OrderedDict
from io import TextIOWrapper
from typing import Generic, Hashable, Optional, TypeVar

patterns = [
    r'(\d+[\.-])+\d+',  # time. eg, 2005-06-14-09.11.51.127157
    # TODO hex
]
DEFAULT_VALUE = 0


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
        self._cache: OrderedDict[T, int] = OrderedDict()

    def __get(self, key: T) -> Optional[T]:
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def insert(self, key: T) -> None:
        if len(self._cache) >= self.capacity:
            self._cache.popitem(last=False)

        self._cache[key] = DEFAULT_VALUE
        self._cache.move_to_end(key)

    def to_list(self) -> list[T]:
        """
        get cached (log clusters) if there is no feedback
        """
        return list(self._cache)

    def clear(self) -> None:
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)

    def __iter__(self):
        # refer to: https://blog.csdn.net/qq_51352578/article/details/125507312
        return self._cache.__iter__()

    def __getitem__(self, item):
        return self.__get(item)


class LogClusterCache(LruCache):
    def __init__(self, capacity: int):
        super().__init__(capacity)

    def insert(self, key: 'LogCluster') -> None:
        if len(self._cache) >= self.capacity:
            log_cluster, _ = self._cache.popitem(last=False)
            # TODO: consider if this log cluster should be removed from trie
            # parent = log_cluster.parent  # trie leaf node
            # assert parent is not None and parent.isEnd
            # parent.remove_log_cluster(log_cluster)

        self._cache[key] = DEFAULT_VALUE
        self._cache.move_to_end(key)


class LogMessagesCache(LruCache):
    def __init__(self, capacity: int):
        super().__init__(capacity)

    def __str__(self):
        return [log_message.get_content() for log_message in self.to_list()]
