import re

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


def plot_cdf(data, cdfs, tps):
    import numpy as np
    import matplotlib.pyplot as plt
    data = np.array(data)
    x = np.arange(0, len(data))
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)
    ax1.scatter(x, data, label='origin', s=5)
    ax2.scatter(x, cdfs, label='cdf', s=5)
    ax3.scatter(x, tps, label='tp', s=5)
    plt.show()
