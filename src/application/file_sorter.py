import os

class FileSorter:
    def __init__(self, rule_engine, file_repo, logger):
        self.rule_engine = rule_engine
        self.file_repo = file_repo
        self.logger = logger

    def sort(self, filepath):
        filename = os.path.basename(filepath)

        dest = self.rule_engine.find_destination(filename)

        if not dest:
            self.logger.log(f"未分類: {filename}")
            return

        self.file_repo.move(filepath, dest)
        self.logger.log(f"{filename} → {dest}")