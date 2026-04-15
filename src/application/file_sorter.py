import os

class FileSorter:
    def __init__(self, rule_engine, file_repo, logger):
        self.rule_engine = rule_engine
        self.file_repo = file_repo
        self.logger = logger

    def sort(self, filepath):
        if not os.path.exists(filepath):
            self.logger.log_event(source_path=filepath, status="SKIPPED", note="ファイルが存在しません")
            return

        filename = os.path.basename(filepath)

        dest = self.rule_engine.find_destination(filename)

        if not dest:
            self.logger.log_event(source_path=filepath, status="UNCLASSIFIED", note="該当ルールなし")
            return

        moved_path = self.file_repo.move(filepath, dest)
        if moved_path:
            moved_filename = os.path.basename(moved_path)
            note = ""
            if moved_filename != filename:
                note = f"重複回避でリネーム: {moved_filename}"

            self.logger.log_event(
                source_path=filepath,
                destination_path=moved_path,
                destination_folder=dest,
                status="MOVED",
                note=note,
            )
            return

        self.logger.log_event(
            source_path=filepath,
            destination_folder=dest,
            status="FAILED",
            note="移動に失敗しました",
        )