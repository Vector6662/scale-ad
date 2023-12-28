import re

from scipy.stats import genextreme
import numpy as np
import matplotlib.pyplot as plt
from logs import LogCluster, FeedBack

def test():
    data = [42, 109, 92, 721, 1, 18, 1, 17, 2, 1, 1, 2, 2, 7, 3, 3, 2, 5, 4, 1, 2, 1, 1, 5, 2, 1, 1, 121, 3, 9, 5, 30,
            208, 2,1, 2, 3, 1, 5, 6, 16, 7, 51, 71, 9, 3, 2, 2, 60, 30, 20, 8, 5, 5, 3, 1, 5, 5, 3, 2, 4, 3, 4, 1, 2, 5, 1, 1,
            2, 5, 7,5, 2, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 3, 21, 4, 2, 1, 1, 17, 16, 23, 6, 9, 1, 20, 5, 2, 1, 1, 1, 1, 1, 1, 1,
            6, 1, 1, 6, 1, 6, 35]

    label = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    data = np.array(data)
    x = np.arange(0, len(data))
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)

    c = -0.5
    mean, var, skew, kurt = genextreme.stats(c, moments='mvsk')

    print('stats:', mean, var, skew, kurt)

    # x = np.linspace(genextreme.ppf(0.01, c), genextreme.ppf(0.99, c), 100)
    cdf = genextreme.cdf(data, c)
    print('cdf:\n', cdf)
    ax1.plot(x, data, 'r-', label='origin')
    ax2.plot(x, cdf, 'k-', label='cdf')

    T = 10  # range from 2 to 10

    tp = cdf ** T / np.sum(cdf) ** T
    print('tp:\n', tp)

    ax3.plot(x, tp, label='tp')

    plt.show()


def detect(log_clusters: list[LogCluster]):
    data = [len(log_cluster.logMessages) for log_cluster in log_clusters]
    c = -0.5
    query_threshold = 0.9
    cdfs = genextreme.cdf(data, c)
    T = 10  # range from 2 to 10
    tps = cdfs ** T / np.sum(cdfs) ** T
    for log_cluster, tp in zip(log_clusters, cdfs):

        if tp > query_threshold:
            samples = "\n".join(log_cluster.logMessages[0:10])
            query_info = (f"\033[41m==================Expert Feedback==================\033[0m\n"
                          f"Does this log message indicate a system anomaly? \n"
                          f"Answer yes or no along with your confidence score ranging from 0 to 1, then explain the reasons.eg: (1,0.8)\n"
                          f"\033[32;49mTEMPLATE:\n{log_cluster.template}\n\033[0m"
                          f"samples:\n{samples}\n....\n"
                          f"\033[32;49m-->\033[0m")
            query = input(query_info)
            m = re.search(r'([01]?)[, ]*(0\.\d*)', query)
            # rag retrival augment generation
            assert m is not None
            g = m.groups()
            assert g[0] is not None or ''
            assert g[1] is not None or ''

            decision, ep = int(g[0]), float(g[1])
            log_cluster.feedback = FeedBack(decision=decision, ep=ep, tp=tp)


