import re
import en_core_web_sm



patterns = [
    r'(\d+[\.-])+\d+', # time. eg, 2005-06-14-09.11.51.127157

]
nlp = en_core_web_sm.load() # load a trained pipeline

class LogMessage:
    def __init__(self) -> None:
        self.line = str # origin log message(one line)
        self.tokens = list(str()) # tokenized log
        self.POSs = list(str()) # part of speech

def read_line(file_path:str) -> list:
    lines = []
    with open(file_path) as file:
        for line in file:
            lines.append(line)
    return lines

def extract_rex(line:str):
    params = []
    for pattern in patterns:
        compiled_re = re.compile(pattern)
        line = compiled_re.sub('<*>', line)
    return line

def tokenize(line:str) -> LogMessage:
    log = LogMessage()
    log.line = line
    doc = nlp(line)
    for token in doc:
        log.tokens.append(token.text)
        log.POSs.append(token.pos_)
    # todo remove any characters that are not letters or numbers
    return log

    # compiled = re.compile(r'\W')
    # tokens = compiled.split(line)
    # tokens = filter(lambda s: s and s.strip(), tokens) # get rid of empty elements
    # return list(tokens)
