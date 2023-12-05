import unittest
from trie import LogCluster


class TestLogCluster(unittest.TestCase):
    def test_match(self):
        log_message = "deleted items: obj1, obj2, obj3, obj4"
        template = "deleted items: <*>"
        log_cluster = LogCluster(template='')
        new_template = log_cluster.extract_template(log_message=log_message, template=template)
