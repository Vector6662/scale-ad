import re
from typing import List, Dict

from preprocess import LogMessage
from collections import OrderedDict

from thefuzz import fuzz
from thefuzz import process
from functools import cmp_to_key

domain_knowledge = ['INFO', 'FATAL', 'ERROR', 'core']

stopwords = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself',
             'yourselves',
             'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
             'their',
             'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is',
             'are', 'was',
             'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
             'the', 'and',
             'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
             'between',
             'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
             'on', 'off',
             'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
             'any', 'both',
             'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
             'than', 'too',
             'very', 'can', 'will', 'just', 'don', 'should', 'now']


def tokenize(seq: str, splitter=' '):
    return re.split(splitter, seq)


def serialize(tokens: list, concat=' '):
    return concat.join(tokens)


class LogCluster:
    def __init__(self, template: str):
        self.template = template
        self.tokenized_template = tokenize(template)
        self.logMessages: list[str] = list()
        self.nWildcard = 0  # number of wildcard(<*>) in the template

    def insert_and_update_template(self, log_message: str):
        self.logMessages.append(log_message)
        self.update(log_message)  # update template based on the new log message

    def update(self, log_message: str):
        """
        update template
        """
        self.tokenized_template = self.extract_template(log_message)
        self.template = serialize(self.tokenized_template)

    def extract_template(self, log_message: str) -> list[str]:
        log_message = re.split(r' ', log_message)
        template = re.split(r' ', self.template)

        common_token_set = set(log_message) & set(
            template)  # identify the common set of tokens shared by both t_i and l_i
        common_token_set.discard('')
        new_tokenized_template = log_message if len(log_message) > len(
            template) else template  # choose the list that has more tokens between 𝑡ˆ and 𝑙ˆ
        new_tokenized_template = list(new_tokenized_template)
        # replace any token in the longer list that is not in the common token set with the placeholder "<*>"
        for i in range(len(new_tokenized_template)):
            if new_tokenized_template[i] not in common_token_set:
                new_tokenized_template[i] = '<*>'
        return new_tokenized_template


# Trie Update
def merge_clusters(log_clusters: list[LogCluster]):
    def cmp(log_cluser: LogCluster):
        items = re.findall(r'<\*>', log_cluser.template)
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


K = 3  # 𝐾 most frequent tokens
token_occurrences = dict()

d = 3  # their first 𝑑 prefix tokens

cmax = 3  # hyperparameter to limit the maximum number of child nodes


def traverse_d_k(log: LogMessage) -> list[str]:
    """
    Traverse by domain knowledge
    """
    # TODO similarity in nlp?
    return [log.get_level()]


def traverse_m_f(log: LogMessage) -> list[str]:
    """
    Traverse by most frequent tokens. English stopwords are discarded
    """
    for token in log.context_tokens:
        token_occurrences[token] = token_occurrences.get(token, 0) + 1
    li = sorted(token_occurrences.items(), key=lambda s: s[1], reverse=True)[0:K][1]
    return [str(li)]


def traverse_prefix(log: LogMessage) -> list[str]:
    """
    Traverse by prefix tokens
    """
    content = log.get_content()
    return content.split(' ')[0:cmax]


traverse_funcs = [traverse_d_k, traverse_m_f, traverse_prefix]

####################
# match
theta_match = 50  # match threshold


def match_exact(log_message: str, log_clusters: set[LogCluster]) -> LogCluster:
    for log_cluster in log_clusters:
        template = log_cluster.template
        template_pattern = template.replace(r'<\*>', r'.*').replace(r'(', '\(').replace(r')', '\)')
        if re.search(template_pattern, log_message) is not None:
            return log_cluster
    return None


def match_partial(log_message: str, log_clusters: set[LogCluster]) -> (LogCluster, int):
    '''
    Partial Match. Use Levenshtein Distance instead of Jaccard similarity at present
    '''
    best_log_cluster, max_score = None, 0
    for logCluster in log_clusters:
        score = fuzz.token_set_ratio(log_message, logCluster.template)
        best_log_cluster = logCluster if score > max_score else best_log_cluster
        max_score = score if score > max_score else max_score
    return best_log_cluster, max_score


class Trie:
    def __init__(self, name) -> None:
        self.name = name
        self.child: dict[str, Trie] = dict()
        self.isEnd = False
        self.logClusters: set[LogCluster] = set()

    def insert(self, log: LogMessage) -> "Trie":
        trie_node = self

        # extract internal nodes
        for func in traverse_funcs:
            internal_tokens = func(log)
            for internal_token in internal_tokens:
                if internal_token not in trie_node.child:
                    trie_node.child[internal_token] = Trie(internal_token)
                trie_node = trie_node.child[internal_token]
                trie_node.isEnd = False
        trie_node.isEnd = True

        # leaf node, match a log cluster then update its template
        log_cluster = trie_node.match(log.get_content())
        trie_node.logClusters.add(log_cluster)  # add the log into trie node
        log_cluster.insert_and_update_template(log.get_content())
        return trie_node

    def match(self, log_message: str) -> LogCluster:
        """
        match, then **remove** a log_cluster from the trie node. should add it again in the following step
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
        level 0 for root node, level 1 for domain knowledge level, level 2 for freq...
        """
        tries = []
        if level == 0:
            return [self]
        for name, child in self.child.items():
            tries.extend(child.search_tries_by_level(level - 1))
        return tries

    def search_clusters_recurse(self) -> list[LogCluster]:
        """
        search clusters recursively
        """
        if self.isEnd:
            return list(self.logClusters)
        log_clusters = []
        for name, child in self.child.items():
            log_clusters.extend(child.search_clusters_recurse())
        return log_clusters
