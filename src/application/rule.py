class Rule:
    def __init__(self, keyword, path):
        self.keyword = keyword.lower()
        self.path = path

    def matches(self, filename):
        return self.keyword in filename.lower()