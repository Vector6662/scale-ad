import re
import en_core_web_sm

patterns = [
    r'(\d+[\.-])+\d+',  # time. eg, 2005-06-14-09.11.51.127157
]
nlp = en_core_web_sm.load()  # load a trained pipeline


class LogMessage:
    def __init__(self) -> None:
        self.line = str()  # origin log message(one line)
        self.headers = list()
        self.data_frame = dict()

        self.context_tokens = list(str())  # tokens generated from CONTEXT
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

    def tokenize(self):
        doc = nlp(self.get_content())
        tokens = [token.text for token in doc]
        POSs = [token.pos_ for token in doc]
        # todo remove any characters that are not letters or numbers
        compiled = re.compile(r'\W')
        for token, pos in zip(tokens, POSs):
            if compiled.match(token) and len(token) == 1:
                continue
            else:
                self.context_tokens.append(token)
                self.context_POSs.append(pos)

    def get_content(self) -> str:
        if 'CONTENT' not in self.data_frame:
            raise ValueError('no field CONTENT in log data frame')
        return self.data_frame['CONTENT']

    def get_level(self) -> str:
        if 'LEVEL' not in self.data_frame:
            raise ValueError('no field LEVEL in log datat frame')
        return self.data_frame['LEVEL']



def read_line(file_path: str) -> list:
    #TODO a better iterator that is friendly with memory
    lines = []
    with open(file_path) as file:
        for line in file:
            lines.append(line)
    return lines


def gen_header(log_format: str):
    compiled = re.compile(r'<\w+>')
    headers = compiled.findall(log_format)
    headers = [header.strip('<').strip('>') for header in headers]
    return headers

    # compiled = re.compile(r'\W')
    # tokens = compiled.split(line)
    # tokens = filter(lambda s: s and s.strip(), tokens) # get rid of empty elements
    # return list(tokens)
