import os
import unicodedata


class Rule:
    def __init__(self, keyword, path):
        self.keyword = self._normalize(keyword)
        self.path = path

    def _normalize(self, text):
        return unicodedata.normalize("NFKC", text).lower()

    def _matches_extension_rule(self, filename):
        if not self.keyword.startswith("ext:"):
            return False

        extension = os.path.splitext(filename)[1].lower().lstrip(".")
        expected = self.keyword.split(":", 1)[1].strip().lstrip(".")
        return extension == expected

    def matches(self, filename):
        normalized_name = self._normalize(filename)
        if self._matches_extension_rule(normalized_name):
            return True
        return self.keyword in normalized_name