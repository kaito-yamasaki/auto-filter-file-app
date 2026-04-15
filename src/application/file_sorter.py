import os

class FileSorter:
    def __init__(self, rule_engine, file_repo, logger):
        self.rule_engine = rule_engine
        self.file_repo = file_repo
        self.logger = logger

    def sort(self, filepath):
        if not os.path.exists(filepath):
            self.logger.log_event(filepath, "", "SKIPPED", "ファイルが存在しません")
            return

        filename = os.path.basename(filepath)

        dest = self.rule_engine.find_destination(filename)

        if not dest:
            self.logger.log_event(filename, "", "UNCLASSIFIED", "該当ルールなし")
            return

        moved_path = self.file_repo.move(filepath, dest)
        if moved_path:
            self.logger.log_event(filename, dest, "MOVED", moved_path)
            return

        self.logger.log_event(filename, dest, "FAILED", "移動に失敗しました")