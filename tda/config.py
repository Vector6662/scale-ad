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
file_path = jenkins_path
log_pattern_re = jenkins_pattern
log_keywords = 'Jenkins'
