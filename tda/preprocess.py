import re
import en_core_web_sm
from logs import LogMessage

patterns = [
    r'(\d+[\.-])+\d+',  # time. eg, 2005-06-14-09.11.51.127157
]



def read_line(file_path: str) -> list:
    # TODO a better iterator that is friendly with memory
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



