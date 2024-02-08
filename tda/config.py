# essential frame is <CONTENT>
import re
from io import TextIOWrapper

bgl_path = './data/BGL/BGL_2k.log'  # reduced log for test， 2k
bgl_pattern = r'\S+ +\d+ +(?P<DATE>\S+) +\S+ +\S+ +\S+ +\S+ +(?P<COMPONENT>\w+) +(?P<LEVEL>\w+) +(?P<CONTENT>.+)'


file_path_bgl2 = './data/bgl2'  # total bgl log, 4747963 lines

jenkins_path = './data/Jenkins/jenkins-test.log'
jenkins_pattern = r'(?P<DATE>\[\S+\]) +(?P<LEVEL>\w+) +(?P<COMPONENT>\w+) +- +((\[[^\[\]]+\] *)|(.+ -+ ))*(?P<CONTENT>[^\n]+)'


file_path = jenkins_path
log_pattern_re = jenkins_pattern
log_keywords = 'Jenkins'




class DataLoader:
    """
    default dataloader
    """

    def __init__(self, log_pattern: str, file_path: str):
        self.log_pattern = log_pattern
        self.file_path = file_path
        self.file_iter: TextIOWrapper = None
        self.headers: list = None
        self.__gen_header()
        self.__gen_lines()

    def __gen_header(self):
        compiled = re.compile(r'<\w+>')
        headers = compiled.findall(self.log_format)
        self.headers = [header.strip('<').strip('>') for header in headers]

    def __gen_lines(self) -> iter:
        self.file_iter = open(self.file_path)

    def get_dataloader(self):
        return self.headers, self.file_iter

    def finish(self):
        self.file_iter.close()

