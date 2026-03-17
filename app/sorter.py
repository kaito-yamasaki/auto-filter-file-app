import os
import shutil
import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 設定ファイル読み込み
with open("rules.json", "r", encoding="utf-8") as f:
    config = json.load(f)

incoming_folder = config["incoming_folder"]
project_root = config["project_root"]
rules = config["rules"]

class DesignSortHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        filename = os.path.basename(filepath).lower()

        for keyword, relative_path in rules.items():
            if keyword.lower() in filename:
                target_folder = os.path.join(project_root, relative_path)
                os.makedirs(target_folder, exist_ok=True)
                shutil.move(filepath, os.path.join(target_folder, os.path.basename(filepath)))
                print(f"{filename} を {target_folder} に移動しました。")
                break  # 一つのルールにマッチしたら処理終了

observer = Observer()
observer.schedule(DesignSortHandler(), incoming_folder, recursive=False)
observer.start()

print("フォルダ監視を開始しました。Ctrl+C で停止できます。")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()