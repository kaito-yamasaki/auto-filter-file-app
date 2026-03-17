import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time

# 設定ファイル名
CONFIG_FILE = "rules.json"

# 初期設定
default_config = {
    "incoming_folder": "",
    "project_root": "",
    "rules": {}
}

# 設定を読み込む
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
else:
    config = default_config

# watchdog 監視用
observer = None

class SortHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        filename = os.path.basename(filepath).lower()
        for keyword, relative_path in config["rules"].items():
            if keyword.lower() in filename:
                target_folder = os.path.join(config["project_root"], relative_path)
                os.makedirs(target_folder, exist_ok=True)
                try:
                    safe_move(filepath, os.path.join(target_folder, os.path.basename(filepath)))
                    log(f"{filename} → {target_folder}")
                except PermissionError:
                    log(f"ERROR: {filename} を移動できませんでした（別プロセスが使用中）")
                break

# ログ表示関数
def log(message):
    log_text.config(state="normal")
    log_text.insert(tk.END, message + "\n")
    log_text.see(tk.END)
    log_text.config(state="disabled")

# フォルダ参照
def browse_folder(entry_widget):
    folder = filedialog.askdirectory()
    if folder:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, folder)

# ルール追加
def add_rule():
    key = keyword_entry.get().strip()
    folder = folder_entry.get().strip()
    if not key or not folder:
        messagebox.showwarning("入力エラー", "キーワードとフォルダを入力してください")
        return
    config["rules"][key] = folder
    update_rule_list()
    save_config()

# ルール削除
def delete_rule():
    selected = rule_list.curselection()
    if not selected:
        return
    key = rule_list.get(selected[0]).split(" → ")[0]
    del config["rules"][key]
    update_rule_list()
    save_config()

# ルールリスト更新
def update_rule_list():
    rule_list.delete(0, tk.END)
    for k, v in config["rules"].items():
        rule_list.insert(tk.END, f"{k} → {v}")

# 設定保存
def save_config():
    config["incoming_folder"] = incoming_entry.get().strip()
    config["project_root"] = project_entry.get().strip()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# 監視開始
def start_watch():
    global observer
    save_config()
    if not config["incoming_folder"] or not config["project_root"]:
        messagebox.showwarning("設定エラー", "監視フォルダとプロジェクトフォルダを設定してください")
        return
    observer = Observer()
    observer.schedule(SortHandler(), config["incoming_folder"], recursive=False)
    observer.start()
    log("監視を開始しました")
    start_button.config(state="disabled")
    stop_button.config(state="normal")

# 監視停止
def stop_watch():
    global observer
    if observer:
        observer.stop()
        observer.join()
        log("監視を停止しました")
        start_button.config(state="normal")
        stop_button.config(state="disabled")

def safe_move(src, dst, retries=5, delay=0.5):
    """ファイルが開かれていてもリトライして移動"""
    for i in range(retries):
        try:
            shutil.move(src, dst)
            return True
        except PermissionError:
            time.sleep(delay)
    # 最後までダメなら例外を出す
    raise PermissionError(f"ファイル移動できません: {src} -> {dst}")

# GUI作成
root = tk.Tk()
root.title("フォルダ自動仕分けアプリ")

tk.Label(root, text="監視フォルダ:").grid(row=0, column=0, sticky="w")
incoming_entry = tk.Entry(root, width=50)
incoming_entry.grid(row=0, column=1)
incoming_entry.insert(0, config.get("incoming_folder",""))
tk.Button(root, text="参照", command=lambda: browse_folder(incoming_entry)).grid(row=0, column=2)

tk.Label(root, text="プロジェクトフォルダ:").grid(row=1, column=0, sticky="w")
project_entry = tk.Entry(root, width=50)
project_entry.grid(row=1, column=1)
project_entry.insert(0, config.get("project_root",""))
tk.Button(root, text="参照", command=lambda: browse_folder(project_entry)).grid(row=1, column=2)

# ルール入力
tk.Label(root, text="キーワード:").grid(row=2, column=0, sticky="w")
keyword_entry = tk.Entry(root)
keyword_entry.grid(row=2, column=1, sticky="w")
tk.Label(root, text="移動先フォルダ（相対パス）:").grid(row=3, column=0, sticky="w")
folder_entry = tk.Entry(root)
folder_entry.grid(row=3, column=1, sticky="w")
tk.Button(root, text="追加", command=add_rule).grid(row=2, column=2, rowspan=2, sticky="ns")
tk.Button(root, text="削除", command=delete_rule).grid(row=2, column=3, rowspan=2, sticky="ns")

# ルールリスト
rule_list = tk.Listbox(root, width=60, height=8)
rule_list.grid(row=4, column=0, columnspan=4)
update_rule_list()

# 開始/停止ボタン
start_button = tk.Button(root, text="監視開始", width=15, command=start_watch)
start_button.grid(row=5, column=0)
stop_button = tk.Button(root, text="監視停止", width=15, command=stop_watch, state="disabled")
stop_button.grid(row=5, column=1)

# ログ
log_text = tk.Text(root, width=70, height=10, state="disabled")
log_text.grid(row=6, column=0, columnspan=4)

# GUIループ
root.mainloop()