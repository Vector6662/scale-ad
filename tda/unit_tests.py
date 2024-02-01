import re
import unittest

from log_structure import LogMessage
from trie import LogCluster, merge_clusters, Trie, traverse_m_f, token_occurrences
import pandas as pd
import process_tda as main
import utils

df = pd.read_csv('../data/BGL/BGL_2k.log_templates.csv')

event_templates = df['EventTemplate']


# print(event_templates)


class TestPreprocess(unittest.TestCase):
    def test_most_frequent_tokens_transformation(self):
        file_path = '../data/BGL/BGL_small.log'  # reduced log for test
        log_format = '<TAG><SEQ><DATE><COMPONENT1><TIMESTAMP><COMPONENT2><COMPONENT3><PRIORITY><LEVEL><CONTENT>'
        headers = utils.gen_header(log_format)
        for line in utils.read_line(file_path):
            log = LogMessage()
            log.preprocess(headers, line)
            for token in log.content_tokens:
                token_occurrences[token] = token_occurrences.get(token, 0) + 1
            li = sorted(token_occurrences.items(), key=lambda s: s[1], reverse=True)[0:3]  # K=3
            print(li)

    def test_java_pattern(self):
        java_pattern = r'(?P<DATE>\S+)  +(?P<LEVEL>\w+) +(?P<PID>\d+) +-+ +\[(?P<THREAD>\w+)\] +(?P<CLASS>\S+) +: +(?P<CONTENT>.+)'
        content = '2024-01-04T16:04:57.400+08:00  INFO 41672 --- [main] c.s.c.services.impl.ServiceCatalogImpl   : Registered service MarketPartnerQueuingService'
        m = re.match(java_pattern, content)
        print(m.groupdict())
        print(m[0])

    def test_extract_jenkins_pattern(self):
        # hint: if there's a [INFO]/[cds] etc., it may have additional contents... but let it alone, too complicated.
        contents = ['[2024-01-12T08:00:35.272Z] info  mavenBuild - [INFO] ',
                    '[2024-01-03T02:05:46.863Z] [Pipeline] echo',
                    '[2024-01-03T02:27:45.916Z] Unstash content: tests',
                    '[2024-01-03T02:06:06.155Z] info  sapPipelineInit - Logging into Vault',
                    '[2024-01-03T02:07:48.094Z] info  mtaBuild - Progress (1): 7.2/60 kB',
                    '[2024-01-03T02:08:03.985Z] info  mtaBuild - ',
                    '[2024-01-03T02:07:52.058Z] info  mtaBuild - [INFO] InstallNodeMojo: No proxy was configured, downloading directly.',
                    '[2024-01-03T02:27:27.683Z] info  codeqlExecuteScan - CodeQL image version: 20231103125425-jdk17-86e411f',
                    '[2024-01-03T02:27:30.203Z] info  codeqlExecuteScan - [2024-01-03 02:27:29] [build-stdout] [INFO] Scanning for projects...',
                    '[2024-01-03T02:27:37.701Z] info  detectExecuteScan - 2024-01-03 02:27:36 UTC INFO  [main] --- Binary Scanner tool will not be run.',
                    ]
        guess = '[TIME] LEVEL COMPONENT - any other pattern can append to: even can be pure test'

        # [2024-01-03T02:27:37.701Z] info detectExecuteScan - 2024-01-03 02:27:36 UTC INFO [main] --- Binary Scanner tool will not be run.
        # [2024-01-03T02:27:30.203Z] info codeqlExecuteScan - [2024-01-03 02:27:29] [build-stdout] [INFO] Scanning for projects...
        pattern1 = r'(?P<DATE>\[\S+\]) +(?P<LEVEL>\w+) +(?P<COMPONENT>\w+) +- +((\[[^\[\]]+\] *)|(.+ -+ ))*(?P<CONTENT>\S+)'
        for content in contents:
            m = re.match(pattern1, content)
            if not m:
                print(content)
                continue
            print(m.groupdict())

    def test_merge_wildcards(self):
        template = '<*> Node card status: <*> <*> <*> <*> <*> <*> <*> <*> is <*> active. Midplane. PGOOD <*> <*> is clear. MPGOOD is OK. MPGOOD <*> <*> is clear. The 2.5 volt rail is OK. The 1.5 volt rail is <*>'
        template_tokens = re.split(r'\s', template)
        new_template_tokens = []
        i = 0
        while i < len(template_tokens):
            if template_tokens[i] != '<*>':
                new_template_tokens.append(template_tokens[i])
                i = i + 1
                continue
            while i < len(template_tokens) and template_tokens[i] == '<*>':
                i = i + 1
            new_template_tokens.append('<*>')
            if i < len(template_tokens):
                new_template_tokens.append(template_tokens[i])
            i = i + 1
        print(new_template_tokens)
    def test_match_words(self):
        cmax = 5
        traverse = {'q', 'w', 'e', 'r', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'}
        prefix_tokens = [token for token, _ in zip(traverse, range(cmax))]
        print(prefix_tokens)


class TestLogCluster(unittest.TestCase):

    def test_merge_demo_log_clusters(self):
        log_clusters = []
        for template in event_templates:
            log_clusters.append(LogCluster(template))

        merge_clusters(log_clusters)

    def test_merge_log_clusteres(self):
        main.process()
        log_clusters = main.root.search_clusters_recurse()
        merge_clusters(log_clusters)

    def test_rex_match(self):
        template = 'ciod: failed to read message prefix on control stream (CioStream socket to <*>:<*>'.replace('(',
                                                                                                                r'\(').replace(
            '<*>', '.*')

        seq = 'ciod: failed to read message prefix on control stream (CioStream socket to a:b'
        match = re.search(template, seq)
        assert match


class TestTrie(unittest.TestCase):
    def test_search_tries_by_level(self):
        main.process()
        print([item.name for item in main.root.search_tries_by_level(2)])
        # share the same "domain knowledge" and "frequent token" internal nodes.

    def test_recursively_search_clusters(self):
        level = 2
        main.process()
        tries = main.root.search_tries_by_level(level)
        print(f'tries in level {level}:', [trie.name for trie in tries])
        print('\n')
        test_trie = tries[-2]
        print('a test trie name: ', test_trie.name)
        clusters = test_trie.search_clusters_recurse()
        print('total clusters:', len(clusters))
        print(''.join([f'{cluster.__hash__()}, {cluster.template}' for cluster in clusters]))

    def test_reconstruct(self):
        main.process()
        main.reconstruct()


def test_cdf():
    data = [42, 109, 92, 721, 1, 18, 1, 17, 2, 1, 1, 2, 2, 7, 3, 3, 2, 5, 4, 1, 2, 1, 1, 5, 2, 1, 1, 121, 3, 9, 5, 30,
            208, 2, 1, 2, 3, 1, 5, 6, 16, 7, 51, 71, 9, 3, 2, 2, 60, 30, 20, 8, 5, 5, 3, 1, 5, 5, 3, 2, 4, 3, 4, 1, 2,
            5, 1, 1,
            2, 5, 7, 5, 2, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 3, 21, 4, 2, 1, 1, 17, 16, 23, 6, 9, 1, 20, 5, 2, 1, 1, 1, 1,
            1, 1, 1,
            6, 1, 1, 6, 1, 6, 35]

    label = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0]
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.stats import genextreme

    data = np.array(data)
    x = np.arange(0, len(data))
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)

    c = -0.5
    mean, var, skew, kurt = genextreme.stats(c, moments='mvsk')

    print('stats:', mean, var, skew, kurt)

    # x = np.linspace(genextreme.ppf(0.01, c), genextreme.ppf(0.99, c), 100)
    cdf = genextreme.cdf(data, c)
    print('cdf:\n', cdf)
    ax1.scatter(x, data, label='origin', s=5)
    ax2.scatter(x, cdf, label='cdf', s=5)

    T = 10  # range from 2 to 10

    tp = cdf ** T / np.sum(cdf) ** T
    print('tp:\n', tp)

    ax3.scatter(x, tp, label='tp', s=5)

    plt.show()