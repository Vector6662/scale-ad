import re
import unittest
from trie import LogCluster, merge_clusters, Trie, traverse_m_f, token_occurrences
import pandas as pd
import process_tda as main
import utils


df = pd.read_csv('../data/BGL/BGL_2k.log_templates.csv')

event_templates = df['EventTemplate']


# print(event_templates)


class TestPreprocess(unittest.TestCase):
    def test_most_frequent_tokens_transformation(self):
        file_path = '../data/BGL/BGL_small.log'  # reduced log for test
        log_format = '<TAG><SEQ><DATE><COMPONENT1><TIMESTAMP><COMPONENT2><COMPONENT3><PRIORITY><LEVEL><CONTENT>'
        headers = preprocess.gen_header(log_format)
        for line in preprocess.read_line(file_path):
            log = preprocess.LogMessage()
            log.preprocess(headers, line)
            for token in log.content_tokens:
                token_occurrences[token] = token_occurrences.get(token, 0) + 1
            li = sorted(token_occurrences.items(), key=lambda s: s[1], reverse=True)[0:3]  # K=3
            print(li)


class TestLogCluster(unittest.TestCase):
    def test_match(self):
        log_message = "deleted items: obj1, obj2, obj3, obj4"
        template = "deleted items: <*>"
        log_cluster = LogCluster(template=template)
        new_template = log_cluster.extract_template(log_message=log_message)
        assert re.split(' ', ' '.join(new_template)) == new_template

    def test_merge_demo_log_clusters(self):
        log_clusters = []
        for template in event_templates:
            log_clusters.append(LogCluster(template))

        merge_clusters(log_clusters)

    def test_merge_log_clusteres(self):
        main.process()
        log_clusters = main.root.search_clusters_recurse()
        merge_clusters(log_clusters)


    def test_sandbox(self):
        template = 'ciod: failed to read message prefix on control stream (CioStream socket to <*>:<*>'.replace('(',
                                                                                                                r'\(').replace(
            '<*>', '.*')

        seq = 'ciod: failed to read message prefix on control stream (CioStream socket to a:b'
        match = re.search(template, seq)
        assert match


class TestTrie(unittest.TestCase):
    def test_search_tries_by_level(self):
        main.process()
        print([item.name for item in main.root.search_tries_by_level(2)])
        # share the same "domain knowledge" and "frequent token" internal nodes.


    def test_recursively_search_clusters(self):
        level = 2
        main.process()
        tries = main.root.search_tries_by_level(level)
        print(f'tries in level {level}:', [trie.name for trie in tries])
        print('\n')
        test_trie = tries[-2]
        print('a test trie name: ', test_trie.name)
        clusters = test_trie.search_clusters_recurse()
        print('total clusters:', len(clusters))
        print(''.join([f'{cluster.__hash__()}, {cluster.template}' for cluster in clusters]))

    def test_reconstruct(self):
        main.process()
        main.reconstruct()


def test_cdf():
    data = [42, 109, 92, 721, 1, 18, 1, 17, 2, 1, 1, 2, 2, 7, 3, 3, 2, 5, 4, 1, 2, 1, 1, 5, 2, 1, 1, 121, 3, 9, 5, 30,
            208, 2, 1, 2, 3, 1, 5, 6, 16, 7, 51, 71, 9, 3, 2, 2, 60, 30, 20, 8, 5, 5, 3, 1, 5, 5, 3, 2, 4, 3, 4, 1, 2,
            5, 1, 1,
            2, 5, 7, 5, 2, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 3, 21, 4, 2, 1, 1, 17, 16, 23, 6, 9, 1, 20, 5, 2, 1, 1, 1, 1,
            1, 1, 1,
            6, 1, 1, 6, 1, 6, 35]

    label = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0]
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.stats import genextreme

    data = np.array(data)
    x = np.arange(0, len(data))
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)

    c = -0.5
    mean, var, skew, kurt = genextreme.stats(c, moments='mvsk')

    print('stats:', mean, var, skew, kurt)

    # x = np.linspace(genextreme.ppf(0.01, c), genextreme.ppf(0.99, c), 100)
    cdf = genextreme.cdf(data, c)
    print('cdf:\n', cdf)
    ax1.scatter(x, data, label='origin', s=5)
    ax2.scatter(x, cdf, label='cdf', s=5)

    T = 10  # range from 2 to 10

    tp = cdf ** T / np.sum(cdf) ** T
    print('tp:\n', tp)

    ax3.scatter(x, tp, label='tp', s=5)

    plt.show()