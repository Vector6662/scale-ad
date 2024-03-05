import re
from threading import Thread
from time import sleep
from typing import Optional

from anomaly_detection import detect_cdf
from config import file_path, log_pattern_re, log_metadata
from exceptions import LogError
from log_structure import LogMessage
from server_apis import render_pyecharts_tree
from trie import Trie, sampling
from utils import LogClusterCache

root: Optional[Trie] = None
lcCache = LogClusterCache(200)  # lru cache of log clusters
logMessages = []


def reconstruct():
    root.reconstruct()
    render_pyecharts_tree("tree-reconstructed.html", root, 'TDA reconstructed')


def detect_worker():
    while True:
        sleep(5)
        print('==============start detection==============')
        # start detection
        detect_cdf(lcCache.to_list())


def process():
    global root
    root = Trie(log_metadata, None)

    pattern = re.compile(log_pattern_re)
    sampling(pattern, file_path)

    # thread for detection
    thr = Thread(target=detect_worker, name='Anomaly Detection Thread')
    # thr.start()

    # main thread, read logs
    with open(file_path) as f:
        for line in f:
            # sleep(0.5)
            # print(f'==============one line coming...==============\t\t{line}')

            try:
                log_message = LogMessage(pattern, line)
            except (LogError, ValueError) as e:
                print(e)
                continue

            trie_node, log_cluster, match_type = root.insert(log_message)
            log_cluster.insert_and_update_template(log_message, match_type)
            log_message.parent = log_cluster  # refer to its parent(type: LogCluster)

            if log_cluster.feedback.decision != 2:
                # todo already has feedback
                pass

            # LRU, add the most frequently used log templates into LRU. only those templates are used in detect().
            #  Moreover, there may need another thread to process this detect simultaneously.
            lcCache.insert(log_cluster)

            # TODO: there may be a fixed size list for logMessages, for this object are only used in Django server API, only part of log messages are been shown
            logMessages.append(log_message)  # all log messages

    data = render_pyecharts_tree("tree_top_bottom.html", root)
    with open('structure.json', 'w') as f:
        f.write(str(data))

    print('tda halt...')
