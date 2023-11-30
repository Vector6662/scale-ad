import re

file_path = 'data/BGL/BGL_2k.log'

patterns = [
    r'(\d+[\.-])+\d+', # time. eg, 2005-06-14-09.11.51.127157

]



def read_line(file_path:str):
    with open(file_path) as file:
        for line in file:
            line = extract_rex(line)
            print('paramlized:', line)
            tokens = tokenize(line)
            print('tokenized:', tokens)

def extract_rex(line:str):
    params = []
    for pattern in patterns:
        compiled_re = re.compile(pattern)
        line = compiled_re.sub('<*>', line)
    return line

def tokenize(line:str):
    compiled = re.compile(r'\W')
    tokens = compiled.split(line)
    tokens = filter(lambda s: s and s.strip(), tokens) # get rid of empty elements
    return list(tokens)



if __name__ == "__main__":
    read_line(file_path)