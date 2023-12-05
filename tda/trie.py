import re
from typing import List

from preprocess import LogMessage
from collections import OrderedDict

from thefuzz import fuzz
from thefuzz import process

domain_knowledge = ['INFO', 'FATAL', 'ERROR', 'core']

stopwords = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 
             'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 
             'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 
             'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 
             'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 
             'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 
             'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 
             'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 
             'very', 'can', 'will', 'just', 'don', 'should', 'now']


class LogCluster:
    def __init__(self, template: str):
        self.template = template
        self.logMessages: list[str] = list()
        self.nWildcard = 0  # number of wildcard(<*>) in the template

    def insert_and_update_template(self, log_message: str):
        self.logMessages.append(log_message)
        self.update(log_message)  # update template based on the new log message

    def update(self, log_message: str):
        """
        update template
        """
        new_template = self.extract_template(self.template, log_message)
        self.template = new_template

    def extract_template(self, log_message: str, template: str):
        log_message = set(re.split(r'\W', log_message))
        template = set(re.split(r'\W', template))
        ret = log_message & template
        ret.remove('')
        return [ret]




K = 3  # 𝐾 most frequent tokens
token_occurrences = dict()

d = 3  # their first 𝑑 prefix tokens

cmax = 2  # hyperparameter to limit the maximum number of child nodes


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

def match_exact(log_message: str, log_clusters: list[LogCluster]) -> LogCluster:
    for log_cluster in log_clusters:
        template = log_cluster.template
        template_pattern = template.replace(r'<\*>', r'.*')
        if re.search(template_pattern, log_message) is not None:
            return log_cluster
    return None


def match_partial(log_message: str, log_clusters: list[LogCluster]) -> (LogCluster, int):
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
    def __init__(self) -> None:
        self.child = dict()
        self.isEnd = False
        self.logClusters: list[LogCluster] = list()

    def insert(self, log: LogMessage) -> "Trie":
        node = self

        # extract internal nodes
        for func in traverse_funcs:
            internal_tokens = func(log)
            for internal_token in internal_tokens:
                if internal_token not in node.child:
                    node.child[internal_token] = Trie()
                node = node.child[internal_token]
                node.isEnd = False
        node.isEnd = True

        # leaf node, match a log cluster then update its template
        log_cluster = node.match(log.get_content())
        log_cluster.insert_and_update_template(log.get_content())
        node.logClusters.append(log_cluster)
        return node

    def match(self, log_message: str) -> LogCluster:
        cluster = match_exact(log_message, self.logClusters)  # exact match
        if cluster is None:
            cluster, score = match_partial(log_message, self.logClusters)  # partial match
            if score < theta_match:
                # The template for this new log cluster is the log message itself, i.e., t_j = l_i
                cluster = LogCluster(log_message)  # no match
        return cluster
