import re
import unittest
from trie import LogCluster, merge_clusters
import pandas as pd

df = pd.read_csv('../data/BGL/BGL_2k.log_templates.csv')

event_templates = df['EventTemplate']

# print(event_templates)


class TestLogCluster(unittest.TestCase):
    def test_match(self):
        log_message = "deleted items: obj1, obj2, obj3, obj4"
        template = "deleted items: <*>"
        log_cluster = LogCluster(template=template)
        new_template = log_cluster.extract_template(log_message=log_message)
        assert re.split(' ', ' '.join(new_template)) == new_template

    def test_merge_log_clusters(self):
        log_clusters = []
        for template in event_templates:
            log_clusters.append(LogCluster(template))

        merge_clusters(log_clusters)

    def test_sandbox(self):
        template = 'ciod: failed to read message prefix on control stream (CioStream socket to <*>:<*>'.replace('(', r'\(').replace('<*>', '.*')

        seq = 'ciod: failed to read message prefix on control stream (CioStream socket to a:b'
        match = re.search(template, seq)
        assert match