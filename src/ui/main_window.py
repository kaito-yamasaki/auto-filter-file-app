from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTextEdit, QListWidget, QFileDialog,
    QTabWidget, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import QTimer
import csv
import os


class MainWindow(QWidget):
    def __init__(self, sorter, config):
        super().__init__()
        self.sorter = sorter
        self.config = config
        self.log_dir = config.get("log_dir", "logs")
        self.log_file = config.get("log_file", "sort_log.csv")
        self.log_path = os.path.join(self.log_dir, self.log_file)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_incoming_files)

        self.setWindowTitle("Auto File Sorter")
        self.setGeometry(200, 200, 900, 500)

        main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.addTab(self.build_main_tab(), "仕分け")
        self.tabs.addTab(self.build_visual_tab(), "可視化")
        self.tabs.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tabs)

        self.setLayout(main_layout)

        self.setStyleSheet(self.dark_theme())
        self.refresh_visualization()

    def build_main_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout()

        # ------------------------
        # 左パネル（設定）
        # ------------------------
        left = QVBoxLayout()

        # 監視フォルダ
        left.addWidget(QLabel("監視フォルダ"))
        incoming_path = self.config.get("incoming", self.config.get("incoming_folder", ""))
        self.incoming_input = QLineEdit(incoming_path)
        btn_incoming = QPushButton("参照")
        btn_incoming.clicked.connect(lambda: self.select_folder(self.incoming_input))

        left.addWidget(self.incoming_input)
        left.addWidget(btn_incoming)

        # 保存先
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

        left.addWidget(QLabel("保存先（相対パス）"))
        self.path_input = QLineEdit()

        btn_add = QPushButton("ルール追加")
        btn_add.clicked.connect(self.add_rule)

        btn_delete = QPushButton("ルール削除")
        btn_delete.clicked.connect(self.delete_rule)

        left.addWidget(self.keyword_input)
        left.addWidget(self.path_input)
        left.addWidget(btn_add)
        left.addWidget(btn_delete)

        # ルール一覧
        left.addWidget(QLabel("ルール一覧"))
        self.rule_list = QListWidget()
        left.addWidget(self.rule_list)

        self.refresh_rules()

        # 操作ボタン
        self.btn_start = QPushButton("開始")
        self.btn_start.clicked.connect(self.start)
        self.btn_end = QPushButton("終了")
        self.btn_end.clicked.connect(self.end)
        self.btn_end.setEnabled(False)

        left.addWidget(self.btn_start)
        left.addWidget(self.btn_end)

        # ------------------------
        # 右パネル（ログ）
        # ------------------------
        right = QVBoxLayout()
        right.addWidget(QLabel("ログ"))

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        right.addWidget(self.log)

        # ------------------------
        # レイアウト結合
        # ------------------------
        main_layout.addLayout(left, 3)
        main_layout.addLayout(right, 5)

        tab.setLayout(main_layout)
        return tab

    def build_visual_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        controls = QHBoxLayout()
        btn_refresh = QPushButton("表示を更新")
        btn_refresh.clicked.connect(self.refresh_visualization)
        controls.addWidget(btn_refresh)
        controls.addStretch()
        layout.addLayout(controls)

        layout.addWidget(QLabel("現在のフォルダ構成"))
        self.directory_tree = QTreeWidget()
        self.directory_tree.setHeaderLabels(["フォルダ / ファイル"])
        layout.addWidget(self.directory_tree, 3)

        layout.addWidget(QLabel("移動履歴（最新100件）"))
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
        layout.addWidget(self.move_history_table, 2)

        tab.setLayout(layout)
        return tab

    def on_tab_changed(self, index):
        if self.tabs.tabText(index) == "可視化":
            self.refresh_visualization()

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
            self.log.append("⚠ 入力不足")
            return

        self.config["rules"][key] = path
        self.refresh_rules()
        self.log.append(f"追加: {key} → {path}")

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
        self.refresh_rules()
        self.log.append(f"削除: {key}")

    # ------------------------
    # ルール一覧更新
    # ------------------------
    def refresh_rules(self):
        self.rule_list.clear()
        for k, v in self.config["rules"].items():
            self.rule_list.addItem(f"{k} → {v}")

    # ------------------------
    # 開始
    # ------------------------
    def start(self):
        incoming_dir = self.incoming_input.text().strip()

        if not incoming_dir or not os.path.isdir(incoming_dir):
            self.log.append("⚠ 監視フォルダが存在しません")
            return

        if self.timer.isActive():
            return

        self.timer.start(1000)
        self.btn_start.setEnabled(False)
        self.btn_end.setEnabled(True)
        self.log.append("監視を開始しました")

    # ------------------------
    # 停止
    # ------------------------
    def end(self):
        if not self.timer.isActive():
            return

        self.timer.stop()
        self.btn_start.setEnabled(True)
        self.btn_end.setEnabled(False)
        self.log.append("監視を停止しました")

    # ------------------------
    # 監視フォルダ処理
    # ------------------------
    def process_incoming_files(self):
        incoming_dir = self.incoming_input.text().strip()

        if not incoming_dir or not os.path.isdir(incoming_dir):
            self.log.append("⚠ 監視フォルダが存在しません")
            self.end()
            return

        files = [
            os.path.join(incoming_dir, name)
            for name in os.listdir(incoming_dir)
            if os.path.isfile(os.path.join(incoming_dir, name))
        ]

        if not files:
            return

        for path in files:
            self.sorter.sort(path)

        self.log.append(f"仕分け実行: {len(files)} 件")
        self.refresh_visualization()

    # ------------------------
    # ダークテーマ
    # ------------------------
    def dark_theme(self):
        return """
        QWidget {
            background-color: #2b2b2b;
            color: white;
        }
        QLineEdit, QTextEdit, QTreeWidget, QTableWidget {
            background-color: #3c3f41;
            color: white;
        }
        QPushButton {
            background-color: #5c5c5c;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #787878;
        }
        QListWidget {
            background-color: #3c3f41;
        }
        """