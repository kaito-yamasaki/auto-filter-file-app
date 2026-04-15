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
        self._ensure_header()

    def _ensure_header(self):
        if os.path.exists(self.log_path):
            return

        with open(self.log_path, "w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["datetime", "filename", "folder", "user", "status", "message"])

    def log(self, message):
        print(message)

    def log_event(self, filename, folder, status, message=""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.log_path, "a", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, filename, folder, self.user_name, status, message])

        print(f"[{timestamp}] {status}: {filename} -> {folder} ({self.user_name}) {message}")