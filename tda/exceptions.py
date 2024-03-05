
class LogError(Exception):
    def __init__(self, log: str, pattern: str):
        super().__init__(self)
        self._error_info = f"\033[41mFailed to match pattern======\033[0m\n{log}\npattern:{pattern}\n\033[41m======\033[0m\n"

    def __str__(self):
        return self._error_info
