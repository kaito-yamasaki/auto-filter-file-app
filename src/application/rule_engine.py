class RuleEngine:
    def __init__(self, rules, default_path=None):
        self.rules = rules
        self.default_path = default_path

    def find_destination(self, filename):
        for rule in self.rules:
            if rule.matches(filename):
                return rule.path
        return self.default_path