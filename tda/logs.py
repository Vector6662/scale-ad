import re
import en_core_web_sm

nlp = en_core_web_sm.load()  # load a trained pipeline


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

        common_token_set = set(log_message) & set(template)  # identify the common set of tokens shared by both t_i and l_i
        common_token_set.discard('')
        new_tokenized_template = log_message if len(log_message) > len(template) else template  # choose the list that has more tokens between 𝑡ˆ and 𝑙ˆ
        new_tokenized_template = list(new_tokenized_template)
        # replace any token in the longer list that is not in the common token set with the placeholder "<*>"
        for i in range(len(new_tokenized_template)):
            if new_tokenized_template[i] not in common_token_set:
                new_tokenized_template[i] = '<*>'
        return new_tokenized_template


class LogMessage:
    def __init__(self) -> None:
        self.line = str()  # origin log message(one line)
        self.headers = list()
        self.data_frame = dict()

        self.content_tokens = list(str())  # tokens generated from CONTEXT
        self.context_POSs = list(str())  # part of speech(generated from CONTEXT as well)

    def preprocess(self, headers: list[str], line: str):
        """
        generate dataframe and tokenize CONTENT field
        """
        self.headers = headers  # headers of dataframe
        self.line = line  # origin log message(per line)
        self.gen_data_frame()
        self.tokenize()

    def gen_data_frame(self):
        data_frame_list = re.split(r' ', self.line, maxsplit=len(self.headers) - 1)
        for header, data_frame in zip(self.headers, data_frame_list):
            self.data_frame[header] = data_frame

    def tokenize1(self):
        doc = nlp(self.get_content())
        tokens = [token.text for token in doc]
        POSs = [token.pos_ for token in doc]
        # todo remove any characters that are not letters or numbers
        compiled = re.compile(r'\W')
        for token, pos in zip(tokens, POSs):
            if compiled.match(token) and len(token) == 1:
                continue
            else:
                self.content_tokens.append(token)
                self.context_POSs.append(pos)

    def tokenize(self):
        # todo remove any characters that are not letters or numbers
        compiled = re.compile(r'\W')

        content = compiled.sub(' ', self.get_content())
        doc = nlp(content)
        tokens = [token.text for token in doc]
        POSs = [token.pos_ for token in doc]
        for token, pos in zip(tokens, POSs):
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