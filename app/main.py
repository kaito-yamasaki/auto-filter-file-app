import os
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

# 監視フォルダ
watch_folder = r"C:\Users\YAMASAKI\Downloads\incoming"

# ファイル名のキーワードごとの仕分け先
rules = {
    "invoice": r"C:\Users\YAMASAKI\Documents\Invoices",
    "report": r"C:\Users\YAMASAKI\Documents\Reports",
    "photo": r"C:\Users\YAMASAKI\Pictures",
}

class SortHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        filename = os.path.basename(filepath).lower()  # 小文字化して検索
        for keyword, target_folder in rules.items():
            if keyword.lower() in filename:
                os.makedirs(target_folder, exist_ok=True)
                shutil.move(filepath, os.path.join(target_folder, os.path.basename(filepath)))
                print(f"{filename} を {target_folder} に移動しました。")
                break  # 一つのルールにマッチしたら処理終了

observer = Observer()
observer.schedule(SortHandler(), watch_folder, recursive=False)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()