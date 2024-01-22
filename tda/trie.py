import re
from typing import List, Dict, Tuple
from io import TextIOWrapper

from log_structure import LogMessage, LogCluster, LogError
from collections import OrderedDict

from thefuzz import fuzz
from thefuzz import process
from functools import cmp_to_key

domain_knowledge = ['INFO', 'FATAL', 'ERROR', 'core']

K = 3  # 𝐾 most frequent tokens
token_occurrences = []
open_class_words = {'ADJ', 'ADV', 'INTJ', 'NOUN', 'PROPN',
                    'VERB'}  # refer to https://universaldependencies.org/u/pos/ , to exclude stopwords

d = 3  # their first 𝑑 prefix tokens

cmax = 3  # hyperparameter to limit the maximum number of child nodes


def sampling(pattern: re.Pattern, file_path: str, bath_size=1000):
    """
    choose first batch_size logs as samples, then extract most frequent tokens, returns a set
    """
    print('========sampling========')
    sample_logs = []
    token_occurrences_dict = dict()
    with open(file_path) as f:
        for line, _ in zip(f, range(bath_size)):
            try:
                log = LogMessage(pattern, line)
            except LogError as e:
                print(e)
                continue

            sample_logs.append(log)
            for token, pos in zip(log.content_tokens, log.context_POSs):
                if pos not in open_class_words:
                    continue
                token_occurrences_dict[token] = token_occurrences_dict.get(token, 0) + 1

    sample_logs = sorted(token_occurrences_dict.items(), key=lambda s: s[1], reverse=True)
    sample_logs = [item[0] for item in sample_logs]
    token_occurrences.extend(sample_logs)


# TODO traverse process should generally based on open class words, NUMs, PRON(i.e. Closed class words)
#  should be excluded within these process. Therefore, rex is just sufficient for this purpose: \w(i.e. words only)
def traverse_d_k(log: LogMessage) -> list[str]:
    """
    Traverse by domain knowledge
    """
    # TODO similarity in nlp?
    return [log.get_level()]


def traverse_m_f(log_message: LogMessage) -> list[str]:
    """
    Traverse by most frequent tokens. English stopwords are discarded
    """
    content_tokens = set(log_message.content_tokens)
    frequent_tokens = []
    count = K
    for token in token_occurrences:
        if count <= 0:
            break
        if token in content_tokens:
            frequent_tokens.append(token)
            count = count - 1
    return [', '.join(frequent_tokens)]


def traverse_prefix(log: LogMessage) -> list[str]:
    """
    Traverse by prefix tokens
    """
    # FIXME: SpaCy determine hex(e.g. 0x1ff2) as an open class words. BTW, is open class words a proper 'judge'?
    prefix_tokens = []
    for token, pos, _ in zip(log.content_tokens, log.context_POSs, range(cmax)):
        if pos not in open_class_words:
            continue
        if re.fullmatch(r'[A-Za-z]+', token) is not None:  # only letter(eg: "demo", "time") can be prefix.
            prefix_tokens.append(token)
    return prefix_tokens


all_traverse_funcs = [traverse_d_k, traverse_m_f, traverse_prefix]

####################
# match: exact, partial, no-match
theta_match = 0.5  # match threshold


def add_escape(value):
    """
    refer to: https://blog.csdn.net/qq_15558143/article/details/123319772
    """
    reserved_chars = r'''?&|!{}[]()^~+'''
    replace = ['\\' + l for l in reserved_chars]
    trans = str.maketrans(dict(zip(reserved_chars, replace)))
    return value.translate(trans)


def match_exact(log_message: str, log_clusters: set[LogCluster]) -> LogCluster:
    for log_cluster in log_clusters:
        template = add_escape(log_cluster.template)
        template = template.replace(r'<*>', r'.*')
        if re.fullmatch(template, log_message):
            return log_cluster
    return None


def match_partial(log_message: str, log_clusters: set[LogCluster]) -> (LogCluster, int):
    """
    Partial Match. Use Levenshtein Distance instead of Jaccard similarity at present
    """
    best_log_cluster, max_score = None, 0
    for logCluster in log_clusters:
        score = fuzz.token_set_ratio(log_message, logCluster.template)
        best_log_cluster = logCluster if score > max_score else best_log_cluster
        max_score = score if score > max_score else max_score
    return best_log_cluster, max_score


class Trie:
    def __init__(self, name: str) -> None:
        self.name = name
        self.children: dict[str, Trie] = dict()
        self.isEnd = False
        self.logClusters: set[LogCluster] = set()

    def insert(self, log_message: LogMessage, funcs=None) -> Tuple["Trie", LogCluster]:
        """
        gross-grained insert via three traverse functions. Then exact inserted into a LogCluster instance.
        returns internal leaf node and log cluster that matches.
        """
        if funcs is None:
            funcs = all_traverse_funcs
        trie_node = self

        # extract internal nodes
        for func in funcs:
            internal_tokens = func(log_message)
            for internal_token in internal_tokens:
                if internal_token not in trie_node.children:
                    trie_node.children[internal_token] = Trie(internal_token)  # create a new node
                trie_node = trie_node.children[internal_token]
                trie_node.isEnd = False
        trie_node.isEnd = True  # leaf node

        # leaf trie node, match a log cluster then update its template
        log_cluster = trie_node.match(log_message.get_content())
        trie_node.logClusters.add(log_cluster)  # add the log into trie node
        log_cluster.insert_and_update_template(log_message.get_content())

        return trie_node, log_cluster

    def match(self, log_message: str) -> LogCluster:
        """
        match, then **remove** a log cluster from the trie node. should add it AGAIN in the following step
        """
        cluster = match_exact(log_message, self.logClusters)  # exact match
        if cluster is None:
            cluster, score = match_partial(log_message, self.logClusters)  # partial match
            if score < theta_match:
                # The template for this new log cluster is the log message itself, i.e., t_j = l_i
                cluster = LogCluster(log_message)  # no match
        self.logClusters.discard(cluster)  # !!!
        return cluster

    def search_tries_by_level(self, level: int) -> list["Trie"]:
        """
        search all trie nodes in a level, e.g. domain knowledge, most frequently used. usually root node call this for the purpose of re-constructing the thie tree.
        level 0 for root node, level 1 for domain knowledge level, level 2 for freq...
        """
        tries = []
        if level == 0:
            return [self]
        for name, child in self.children.items():
            tries.extend(child.search_tries_by_level(level - 1))
        return tries

    def search_clusters_recurse(self) -> list[LogCluster]:
        """
        search ALL log clusters recursively, if this trie isEnd == False, then search its all child nodes until isEnd == True, return all log clusters
        """
        if self.isEnd:
            return list(self.logClusters)
        log_clusters = []
        for name, child in self.children.items():
            log_clusters.extend(child.search_clusters_recurse())
        return log_clusters

    def reconstruct(self, level=2):
        """
        re-construct trie start by this trie node instance
        """
        if level == 0:
            self.update_trie()
        else:
            for name, child in self.children.items():
                child.reconstruct(level - 1)

    def update_trie(self, traverse_func=traverse_prefix):
        """
        update trie. a part of reconstruct.
        search ALL log clusters under this trie node or its children recursively, then clear its all child nodes, finally re-construct its child nodes
        traverse_func: assign traverse function
        """
        log_clusters = self.search_clusters_recurse()  # gather all log clusters under this node recursively
        assert self.isEnd == False
        self.children = dict()  # clear all child trie nodes, then re-construct
        for log_cluster in log_clusters:
            node = self
            # generate a log message based on a template
            log_message = LogMessage(template=log_cluster.template)
            prefix_tokens = traverse_func(log_message)
            for token in prefix_tokens:
                if token not in node.children:
                    node.children[token] = Trie(token)
                node = node.children[token]
                node.isEnd = False
            node.isEnd = True
            node.logClusters.add(log_cluster)

    def extract_recently_used_templates(self):
        """
        LRU strategy, limit the number of log templates considered for fitting the GEV distribution
        """
        log_clusters = self.search_clusters_recurse()
        sorted(log_clusters, key=lambda log: log.recent_used_timestamp, reverse=True)

    def remove_log_cluster(self, log_cluster: LogCluster):
        self.logClusters.remove(log_cluster)

    # Trie Update


def merge_clusters(log_clusters: list[LogCluster]):
    def cmp(log_cluster: LogCluster):
        items = re.findall(r'<\*>', log_cluster.template)
        return len(items)

    sorted_log_clusters = sorted(log_clusters, key=cmp,
                                 reverse=True)  # no arg 'cmp' in python 3+. refer to: https://blog.csdn.net/gongjianbo1992/article/details/107324871

    # for log_cluster in sorted_log_clusters:
    #     print(log_cluster.template)
    for i in range(len(sorted_log_clusters) - 1):
        # print(sorted_log_clusters[i].template)
        template = sorted_log_clusters[i].template.replace('<*>', '.*')
        template = template.replace('(', r'\(').replace(')', r'\)')
        complied = re.compile(template)
        if re.search(template, sorted_log_clusters[i + 1].template):
            print('GOOD!')
