"""
Log Data Structures, including LogMessage(wrapper of each log message. Each line is a log message), LogCluster

"""
import re
from time import time
import en_core_web_sm

nlp = en_core_web_sm.load()  # load a trained pipeline


class LogError(Exception):
    def __init__(self, log: str, pattern: str):
        super().__init__(self)
        self.error_info = f"\033[41mFailed to match pattern======\033[0m\n{log}\npattern:{pattern}\n\033[41m======\033[0m\n"

    def __str__(self):
        return self.error_info


def merge_adjacent_wildcards(template_tokens: list[str]):
    """
    merge adjacent <*>s
    """
    new_tokenized_template = []
    i = 0
    while i < len(template_tokens):
        if template_tokens[i] != '<*>':
            new_tokenized_template.append(template_tokens[i])
            i = i + 1
            continue
        while i < len(template_tokens) and template_tokens[i] == '<*>':
            i = i + 1
        new_tokenized_template.append('<*>')
        if i < len(template_tokens):
            new_tokenized_template.append(template_tokens[i])
        i = i + 1
    return new_tokenized_template


def extract_template(log_message: str, template: str) -> list[str]:
    """
    extract a new template between the incoming log cluster and existed template
    """
    log_message = re.split(r' ', log_message)
    template = re.split(r' ', template)
    # identify the common set of tokens shared by both t_i and l_i
    common_token_set = set(log_message) & set(template)
    common_token_set.discard('')
    # choose the list that has more tokens between 𝑡ˆ and 𝑙ˆ
    new_tokenized_template = log_message if len(log_message) > len(template) else template
    new_tokenized_template = list(new_tokenized_template)
    # replace any token in the longer list that is not in the common token set with the placeholder "<*>"
    for i in range(len(new_tokenized_template)):
        if new_tokenized_template[i] not in common_token_set:
            new_tokenized_template[i] = '<*>'
    return new_tokenized_template


def serialize(tokenized_template: list[str]):
    template = ' '.join(tokenized_template)
    # template = re.sub(r' *<\*> *', '<*>', template)
    return template


class LogCluster:
    def __init__(self, template: str):
        self.template: str = template
        self.tokenized_template = re.split(r'\s', template)
        self.compiled_template: re.Pattern = None
        self.logMessages: list[str] = list()
        self.nWildcard: int = 0  # number of wildcard(<*>) in the template
        self.ground_truth: float = 0
        self.recent_used_timestamp = None
        self.update_time()
        self.feedback = FeedBack(decision=2, ep=-1, tp=-1)  # instance of Feedback, default unknown
        self.parent: 'Trie' = None

    def insert_and_update_template(self, log_message: str):
        self.logMessages.append(log_message)
        # update template based on the new log message
        self.tokenized_template = extract_template(log_message, self.template)
        # merge adjacent "<*>"s
        self.tokenized_template = merge_adjacent_wildcards(self.tokenized_template)

        # serialize
        self.template = serialize(self.tokenized_template)

        # cache pattern
        pattern = re.escape(self.template)
        pattern = pattern.replace('<*>', '.*')
        self.compiled_template = re.compile(pattern)

        self.update_time()

    def update_time(self):
        self.recent_used_timestamp = int(time())


class LogMessage:
    def __init__(self, pattern: re.Pattern = None, line: str = None, template: str = None) -> None:
        """
        pattern: compiled input log line pattern
        line: origin log line
        """
        self.data_frame = dict()
        self.content_tokens = list(str())  # tokens generated from CONTEXT
        self.context_POSs = list(str())  # part of speech(generated from CONTEXT as well)
        self.log_cluster: LogCluster = None  # the log cluster which this log message belongs to

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

    def __gen_data_frame(self):
        m = self.pattern.match(self.line)
        if not m:
            raise LogError(self.line, str(self.pattern))
        gd = m.groupdict()
        assert gd['CONTENT'], gd['LEVEL']
        self.data_frame.update(gd)

    def __tokenize(self):
        # remove any characters that are not letters or numbers
        compiled = re.compile(r'\W')  # [^A-Za-z0-9_] not character, number, _
        content = compiled.sub(' ', self.get_content())
        # then analyze part-of-speech of each word
        doc = nlp(content)
        tokens = [token.text for token in doc]
        part_of_speeches = [token.pos_ for token in doc]
        for token, pos in zip(tokens, part_of_speeches):
            self.content_tokens.append(token)
            self.context_POSs.append(pos)

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

    def __init__(self, decision: int, ep: float, tp: float, reason='desc...'):
        self.decision = decision  # 1 indicates anomaly, 0 indicated normal, 2 unknown
        self.ep = ep  # confidence score given by experts
        self.tp = tp  # anomaly score by GEV
        self.p = self.compute_integrate()
        self.reason = reason

    def compute_integrate(self):
        """
        compute an integrated anomaly score 𝑝, which is a weighted average of TDA’s output and the expert’s feedback, where we use the expert’s confidence as the weight.
        """
        assert self.decision == 0 or 1
        if self.decision == 1:
            p = self.ep + (1 - self.ep) * self.tp
        else:
            p = 1 - (self.ep + (1 - self.ep) * (1 - self.tp))
        return p
