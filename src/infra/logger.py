import csv
import getpass
import os
from datetime import datetime


class Logger:
    def __init__(self, log_dir="logs", log_file_name="sort_log.csv", user_name=None):
        self.log_dir = log_dir
        self.log_file_name = log_file_name
        self.user_name = user_name or getpass.getuser()

        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, self.log_file_name)
        self.header = [
            "datetime",
            "status",
            "filename",
            "source_path",
            "destination_path",
            "destination_folder",
            "user",
            "note"
        ]
        self._ensure_header()

    def _ensure_header(self):
        if os.path.exists(self.log_path):
            with open(self.log_path, "r", encoding="utf-8-sig", newline="") as file:
                reader = csv.reader(file)
                first_row = next(reader, None)

            if first_row == self.header:
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.log_dir, f"legacy_{timestamp}_{self.log_file_name}")
            os.replace(self.log_path, backup_path)

        with open(self.log_path, "w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(self.header)

    def log(self, message):
        print(message)

    def log_event(self, source_path, destination_path="", destination_folder="", status="INFO", note=""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = os.path.basename(source_path) if source_path else ""

        with open(self.log_path, "a", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                timestamp,
                status,
                filename,
                source_path,
                destination_path,
                destination_folder,
                self.user_name,
                note,
            ])

        print(
            f"[{timestamp}] {status}: {filename} | from={source_path} | to={destination_path} | "
            f"folder={destination_folder} | user={self.user_name} | {note}"
        )