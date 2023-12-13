import re
import unittest
from trie import LogCluster, merge_clusters, Trie, traverse_m_f, token_occurrences
import pandas as pd
import main
import preprocess

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

