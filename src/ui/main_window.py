from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QListWidget, QFileDialog,
    QTabWidget,
    QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
import csv
import json
import os
from pathlib import Path


class DropArea(QLabel):
    def __init__(self, on_files_dropped, parent=None):
        super().__init__(parent)
        self.on_files_dropped = on_files_dropped
        self.setAcceptDrops(True)
        self.setObjectName("dropArea")
        self.setText("ここにファイルをドラッグ＆ドロップ")
        self.setMinimumHeight(100)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        file_paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        self.on_files_dropped(file_paths)
        event.acceptProposedAction()


class MainWindow(QWidget):
    def __init__(self, sorter, config):
        super().__init__()
        self.sorter = sorter
        self.config = config
        self.log_dir = config.get("log_dir", "logs")
        self.log_file = config.get("log_file", "sort_log.csv")
        self.log_path = os.path.join(self.log_dir, self.log_file)
        self.config_path = Path(__file__).resolve().parents[2] / "rules.json"

        self.setWindowTitle("Auto File Sorter")
        self.setGeometry(200, 200, 900, 500)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.build_main_tabs())

        self.setLayout(main_layout)

        self.setStyleSheet(self.dark_theme())
        self.refresh_visualization()

    def build_main_tabs(self):
        tabs = QTabWidget()
        tabs.addTab(self.build_sort_rule_tab(), "仕分け・ルール")
        tabs.addTab(self.build_visualization_tab(), "フォルダ構成・移動履歴")
        return tabs

    def build_sort_rule_tab(self):
        tab = QWidget()
        left = QVBoxLayout()

        left.addWidget(QLabel("ドラッグ＆ドロップ仕分け"))
        self.drop_area = DropArea(self.process_dropped_files, self)
        left.addWidget(self.drop_area)

        left.addWidget(QLabel("保存先ルート"))
        root_path = self.config.get("root", self.config.get("project_root", ""))
        self.root_input = QLineEdit(root_path)
        btn_root = QPushButton("参照")
        btn_root.clicked.connect(lambda: self.select_folder(self.root_input))

        left.addWidget(self.root_input)
        left.addWidget(btn_root)

        # ルール入力
        left.addWidget(QLabel("キーワード"))
        self.keyword_input = QLineEdit()
        left.addWidget(self.keyword_input)

        left.addWidget(QLabel("保存先（相対パス）"))
        self.path_input = QLineEdit()
        left.addWidget(self.path_input)

        btn_add = QPushButton("ルール追加")
        btn_add.clicked.connect(self.add_rule)

        btn_delete = QPushButton("ルール削除")
        btn_delete.clicked.connect(self.delete_rule)

        left.addWidget(btn_add)
        left.addWidget(btn_delete)

        # ルール一覧
        right = QVBoxLayout()

        right.addWidget(QLabel("ルール一覧"))
        self.rule_list = QListWidget()
        right.addWidget(self.rule_list)

        self.refresh_rules()
        right.addStretch()

        # 全体のレイアウト
        layout = QHBoxLayout()
        layout.addLayout(left, 3)
        layout.addLayout(right, 5)
        tab.setLayout(layout)

        return tab

    def build_visualization_tab(self):
        tab = QWidget()
        left = QVBoxLayout()

        controls = QHBoxLayout()
        btn_refresh = QPushButton("表示を更新")
        btn_refresh.clicked.connect(self.refresh_visualization)
        controls.addWidget(btn_refresh)
        controls.addStretch()
        left.addLayout(controls)

        left.addWidget(QLabel("現在のフォルダ構成"))
        self.directory_tree = QTreeWidget()
        self.directory_tree.setHeaderLabels(["フォルダ / ファイル"])
        left.addWidget(self.directory_tree, 1)

        right = QVBoxLayout()
        right.addWidget(QLabel("移動履歴（最新100件）"))
        self.move_history_table = QTableWidget()
        self.move_history_table.setColumnCount(5)
        self.move_history_table.setHorizontalHeaderLabels([
            "日時", "ファイル名", "移動先（ルール）", "ユーザー名", "備考"
        ])
        self.move_history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.move_history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.move_history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.move_history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.move_history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        right.addWidget(self.move_history_table, 1)

        # 全体のレイアウト
        layout = QHBoxLayout()
        layout.addLayout(left, 3)
        layout.addLayout(right, 5)
        tab.setLayout(layout)
        return tab

    def refresh_visualization(self):
        self.refresh_directory_tree()
        self.refresh_move_history()

    def refresh_directory_tree(self):
        self.directory_tree.clear()

        root_path = self.root_input.text().strip()
        if not root_path:
            root_item = QTreeWidgetItem(["保存先ルートが未設定です"])
            self.directory_tree.addTopLevelItem(root_item)
            return

        if not os.path.isdir(root_path):
            root_item = QTreeWidgetItem([f"フォルダが存在しません: {root_path}"])
            self.directory_tree.addTopLevelItem(root_item)
            return

        root_item = QTreeWidgetItem([root_path])
        self.directory_tree.addTopLevelItem(root_item)
        self.add_tree_items(root_item, root_path)
        self.directory_tree.expandToDepth(1)

    def add_tree_items(self, parent_item, path):
        try:
            entries = sorted(
                os.listdir(path),
                key=lambda name: (not os.path.isdir(os.path.join(path, name)), name.lower())
            )
        except OSError:
            return

        for name in entries:
            full_path = os.path.join(path, name)
            child = QTreeWidgetItem([name])
            parent_item.addChild(child)
            if os.path.isdir(full_path):
                self.add_tree_items(child, full_path)

    def refresh_move_history(self):
        self.move_history_table.setRowCount(0)

        if not os.path.exists(self.log_path):
            return

        try:
            with open(self.log_path, "r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                moved_rows = [row for row in reader if row.get("status") == "MOVED"]
        except OSError:
            return

        recent_rows = moved_rows[-100:]
        recent_rows.reverse()

        self.move_history_table.setRowCount(len(recent_rows))
        for row_index, row in enumerate(recent_rows):
            self.move_history_table.setItem(row_index, 0, QTableWidgetItem(row.get("datetime", "")))
            self.move_history_table.setItem(row_index, 1, QTableWidgetItem(row.get("filename", "")))
            self.move_history_table.setItem(row_index, 2, QTableWidgetItem(row.get("destination_folder", "")))
            self.move_history_table.setItem(row_index, 3, QTableWidgetItem(row.get("user", "")))
            self.move_history_table.setItem(row_index, 4, QTableWidgetItem(row.get("note", "")))

    # ------------------------
    # フォルダ選択
    # ------------------------
    def select_folder(self, field):
        folder = QFileDialog.getExistingDirectory()
        if folder:
            field.setText(folder)

    # ------------------------
    # ルール追加
    # ------------------------
    def add_rule(self):
        key = self.keyword_input.text().strip()
        path = self.path_input.text().strip()

        if not key or not path:
            self.append_message("⚠ 入力不足")
            return

        self.config["rules"][key] = path
        self.save_config_file()
        self.refresh_rules()
        self.append_message(f"追加: {key} → {path}")

    # ------------------------
    # ルール削除
    # ------------------------
    def delete_rule(self):
        selected = self.rule_list.currentItem()
        if not selected:
            return

        text = selected.text()
        key = text.split(" → ")[0]

        del self.config["rules"][key]
        self.save_config_file()
        self.refresh_rules()
        self.append_message(f"削除: {key}")

    def save_config_file(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as file:
                json.dump(self.config, file, ensure_ascii=False, indent=2)
        except OSError as error:
            self.append_message(f"⚠ rules.json 保存失敗: {error}")

    # ------------------------
    # ルール一覧更新
    # ------------------------
    def refresh_rules(self):
        self.rule_list.clear()
        for k, v in self.config["rules"].items():
            self.rule_list.addItem(f"{k} → {v}")

    def process_dropped_files(self, file_paths):
        if not file_paths:
            self.append_message("⚠ ドロップされたファイルがありません")
            return

        valid_files = [path for path in file_paths if os.path.isfile(path)]
        skipped = len(file_paths) - len(valid_files)

        if not valid_files:
            self.append_message("⚠ ファイルのみドロップできます")
            return

        for path in valid_files:
            self.sorter.sort(path)

        message = f"ドラッグ＆ドロップ仕分け: {len(valid_files)} 件"
        if skipped > 0:
            message += f"（フォルダ等を {skipped} 件スキップ）"
        self.append_message(message)
        self.refresh_visualization()

    def append_message(self, message):
        print(message)

    # ------------------------
    # ダークテーマ
    # ------------------------
    def dark_theme(self):
        return """
        QWidget {
            background-color: #2b2b2b;
            color: white;
            font-size: 24px;
        }
        QLineEdit, QTreeWidget, QTableWidget {
            background-color: #3c3f41;
            color: white;
        }
        QPushButton {
            background-color: #5c5c5c;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #787878;
        }
        QListWidget {
            background-color: #3c3f41;
        }
        #dropArea {
            border: 2px dashed #787878;
            border-radius: 6px;
            background-color: #3c3f41;
            padding: 10px;
        }
        """