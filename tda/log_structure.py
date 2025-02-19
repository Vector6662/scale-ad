"""
Log Data Structures, including LogMessage(wrapper of each log message. Each line is a log message), LogCluster

"""
import re
from time import time
from typing import Optional

import en_core_web_sm

from config import EXACT_MATCH, NO_MATCH, PARTIAL_MATCH, TRA_TYPE_most_frequent_tokens, TRA_TYPE_prefix_tokens, TRA_TYPE_domain_knowledge
from exceptions import LogError
from utils import LogMessagesCache

nlp = en_core_web_sm.load()  # load a trained pipeline

# refer to https://universaldependencies.org/u/pos/ , to exclude stopwords
open_class_words = {'ADJ', 'ADV', 'INTJ', 'NOUN', 'PROPN', 'VERB'}



def tokenize(content: str):
    """
    ONLY interface to tokenize string, because there must be ONLY one standard to tokenize.
    For better performance, here only tokenize a string split by spaces, i.e.: currently, don't consider chars like '(', ')', '[', etc.
    """
    tokens = re.split(r'(\s+)', content)
    return tokens


def serialize(tokens: list[str]):
    return ''.join(tokens)


def merge_adjacent_wildcards(template_tokens: list[str]) -> [list[str], str]:
    """
    merge adjacent <*>s.
    spaces between '<*>' should be replaced. e.g. ['<*>', ' ', ' \t\t', '<*>'] ---> ['<*>']
    """
    # FIXME: there's risk on serialize -> tokenize. Ideally, only one traverse direction: tokenize-> serialize
    template = re.sub(r'<\*>(\s|(<\*>))*<\*>', '<*>', serialize(template_tokens))
    return tokenize(template), template


def extract_template(log_message: 'LogMessage', tokenized_template: list[str]) -> list[str]:
    """
    extract a new template between the incoming log cluster and existed template
    """
    log_message = log_message.content_tokens
    # identify the common set of tokens shared by both t_i and l_i
    common_token_set = set(log_message) & set(tokenized_template)
    common_token_set.discard('')
    # choose the list that has more tokens between 𝑡ˆ and 𝑙ˆ
    new_tokenized_template = log_message if len(log_message) > len(tokenized_template) else tokenized_template
    new_tokenized_template = list(new_tokenized_template)
    # replace any token in the longer list that is not in the common token set with the placeholder "<*>"
    for i in range(len(new_tokenized_template)):
        if new_tokenized_template[i] not in common_token_set:
            new_tokenized_template[i] = '<*>'
    return new_tokenized_template


class LogCluster:
    def __init__(self, tokenized_template: list[str]):
        self.tokenized_template: list[str] = tokenized_template
        self.template: str = serialize(tokenized_template)
        self.logMessagesCache: LogMessagesCache = LogMessagesCache(300)
        self.nWildcard: int = 0  # number of wildcard(<*>) in the template
        self.ground_truth: float = 0
        self.recent_used_timestamp = None
        self.update_time()
        self.feedback = FeedBack(decision=-1, ep=-1, tp=-1)  # instance of Feedback, default unknown
        self._parent: Optional['Trie'] = None
        self.metadata: dict[str, str] = dict()  # names from parent to root trie nodes, also includes field 'template' of its own

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, trie_node: 'Trie'):
        self._parent = trie_node
        while trie_node:
            self.metadata[trie_node.node_type] = trie_node.name if trie_node.node_type not in self.metadata else self.metadata[trie_node.node_type]+f', {trie_node.name}'
            trie_node = trie_node.parent

    def insert_and_update_template(self, log_message: 'LogMessage', match_type: int):
        """
        insert log message into the corresponding log cluster, then update log cluster's template, only if match type is not EXACT_MATCH.
        for EXACT_MATCH, not necessary to update template.
        """
        self.update_time()
        self.logMessagesCache.insert(log_message)
        # exact match, then no need to update template
        if match_type == EXACT_MATCH:
            return
        # update template based on the new log message
        self.tokenized_template = extract_template(log_message, self.tokenized_template)
        # merge adjacent "<*>"s
        self.tokenized_template, self.template = merge_adjacent_wildcards(self.tokenized_template)

    def update_time(self):
        self.recent_used_timestamp = int(time())

    def get_log_messages(self) -> list[str]:
        """
        get CONTENT of log messages under this log cluster
        """
        return [log_message.get_content() for log_message in self.logMessagesCache.to_list()]


class LogMessage:
    def __init__(self, pattern: re.Pattern = None, line: str = None, template: str = None) -> None:
        """
        pattern: compiled input log line pattern
        line: origin log line
        """
        self.data_frame = dict()
        self.traverse_tokens: Optional[dict] = None  # tokens used in traverse internal nodes
        self.content_tokens = list(str())  # tokens generated from CONTEXT
        self.parent: Optional[LogCluster] = None  # the log cluster which this log message belongs to

        # update trie process will call it too. in this condition, only requires log cluster template parameter.
        if template:
            self.data_frame['CONTENT'] = template
            self.__tokenize()
            return

        assert pattern, line
        self.pattern = pattern
        self.line = line.replace('\n', '')  # origin log message, remove \n
        # preprocess. generate dataframe and tokenize CONTENT field
        self.__gen_data_frame()
        self.__tokenize()
        # TODO: add context to every log message. maybe 10 log entry before and after this message

    def __gen_data_frame(self):
        m = self.pattern.match(self.line)
        if not m:
            raise LogError(self.line, str(self.pattern))
        gd = m.groupdict()
        # check if the data frame CONTENT only contains space or non-words, eg, '--------', ' '.
        if re.fullmatch(r'\W*', gd['CONTENT']):
            raise ValueError(f"field CONTENT: [{gd['CONTENT']}], or LEVEL:[{gd['LEVEL']}] is empty")
        self.data_frame.update(gd)

    def __tokenize(self):
        # remove any characters that are not letters or numbers
        self.content_tokens = tokenize(self.get_content())
        # generate tokens by nlp, filter out open class words, use these tokens in traverse internal nodes stage

        # FIXME: Spacy defect.
        #  Filer out Open Class Words is not enough, eg.
        #    '0x0b85eee0'                                --> PROPN;
        #    'generating core.2275'                           --> [VERB, PROPN]
        #    'machine[NOUN] check[NOUN]:[PUNCT] i[PRON]-[VERB]fetch[VERB]......................[PUNCT]0[NUM]'   Possible solution: filter out non-words? like '-' here
        #  Only words(r'[A-Za-z]+') can be put into traverse tokens? so NLP is not necessary?

        # TODO: Further optimization: here, I just get rid of numbers, or words that contains numbers, e.g.
        #    "CE sym 2, at 0x0b85eee0, mask 0x05, core.3947358" ---> "CE sym , at , mask , core.".
        #    "CioStream socket to 172.16.96.116:33370'"         ---> "CioStream socket to ...:'"
        #  then the traverse tokens won't contain any numbers.
        #  However, this is not an elegant solution. Optimization may be processed after researching Spacy. I think patterns like hex '0x05' can be identified as NUM.

        # TODO: There may be another way to fix this: remove PROPN from open_class_words?
        content = re.sub(r'\w*\d+\w*', '', self.get_content())
        self.traverse_tokens = {token.text: token.pos_ for token in nlp(content) if token.pos_ in open_class_words}
        pass

    def get_content(self) -> str:
        if 'CONTENT' not in self.data_frame:
            raise ValueError('no field CONTENT in log data frame')
        return self.data_frame['CONTENT']

    def get_level(self) -> str:
        if 'LEVEL' not in self.data_frame:
            raise ValueError('no field LEVEL in log datat frame')
        return self.data_frame['LEVEL']


class FeedBack:
    """
    expert feed back, including on-call engineers, GPT
    """

    def __init__(self, ep: float, tp: float, decision: int = -1, reason='no feedback yet'):
        """
        -1: initial state, means haven't submitted to expert for feedback.
        others have been submitted to expert, but may no feedback yet:
        1 indicates anomaly, 0 indicated normal
        """
        self.decision: int = decision
        self.ep = ep  # confidence score given by experts
        self.tp = tp  # anomaly score by GEV
        self.p = self._compute_integrate()
        self.reason: str = reason
        self.committer: Optional[str] = None  # the one made this decision

    def _compute_integrate(self):
        """
        compute an integrated anomaly score 𝑝, which is a weighted average of TDA’s output and the expert’s feedback, where we use the expert’s confidence as the weight.
        """
        assert self.decision == 0 or 1
        if self.decision == 1:
            p = self.ep + (1 - self.ep) * self.tp
        else:
            p = 1 - (self.ep + (1 - self.ep) * (1 - self.tp))
        return p
