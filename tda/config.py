# essential frame is <CONTENT>
import re
from io import TextIOWrapper

bgl_path = './data/BGL/BGL_2k.log'  # reduced log for test， 2k
bgl_pattern = r'\S+ +\d+ +(?P<DATE>\S+) +\S+ +\S+ +\S+ +\S+ +(?P<COMPONENT>\w+) +(?P<LEVEL>\w+) +(?P<CONTENT>.+)'

bgl2_path = './data/bgl2'  # total bgl log, 4747963 lines
bgl2_pattern = bgl_pattern

jenkins_path = './data/Jenkins/semantic-sdk-release.log'
jenkins_pattern = r'(?P<DATE>\[\S+\]) +(?P<LEVEL>\w+) +(?P<COMPONENT>\w+) +- +((\[[^\[\]]+\] *)|(.+ -+ ))*(?P<CONTENT>[^\n]+)'

# config interface
file_path = bgl_path
log_pattern_re = bgl2_pattern
log_metadata = 'Jenkins, groovy, devops'

################################################
# Constant Variables used cross py files under tda directory

# traverse function types' name
TRA_TYPE_domain_knowledge = 'domain knowledge'
TRA_TYPE_most_frequent_tokens = 'most frequent tokens'
TRA_TYPE_prefix_tokens = 'prefix tokens'

# match types of log message match log clusters
EXACT_MATCH = 0
PARTIAL_MATCH = 1
NO_MATCH = 2
################################################
