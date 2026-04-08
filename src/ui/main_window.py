from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTextEdit, QListWidget, QFileDialog
)
from PyQt6.QtCore import Qt


class MainWindow(QWidget):
    def __init__(self, sorter, config):
        super().__init__()
        self.sorter = sorter
        self.config = config

        self.setWindowTitle("Auto File Sorter")
        self.setGeometry(200, 200, 900, 500)

        main_layout = QHBoxLayout()

        # ------------------------
        # 左パネル（設定）
        # ------------------------
        left = QVBoxLayout()

        # 監視フォルダ
        left.addWidget(QLabel("監視フォルダ"))
        self.incoming_input = QLineEdit(config.get("incoming_folder", ""))
        btn_incoming = QPushButton("参照")
        btn_incoming.clicked.connect(lambda: self.select_folder(self.incoming_input))

        left.addWidget(self.incoming_input)
        left.addWidget(btn_incoming)

        # 保存先
        left.addWidget(QLabel("保存先ルート"))
        self.root_input = QLineEdit(config.get("project_root", ""))
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
        btn_test = QPushButton("テスト仕分け")
        btn_test.clicked.connect(self.test_sort)

        left.addWidget(btn_test)

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

        self.setLayout(main_layout)

        # ダークテーマ
        self.setStyleSheet(self.dark_theme())

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
    # テスト処理
    # ------------------------
    def test_sort(self):
        test_path = self.incoming_input.text() + "/_test.txt"
        self.sorter.sort(test_path)
        self.log.append("テスト実行")

    # ------------------------
    # ダークテーマ
    # ------------------------
    def dark_theme(self):
        return """
        QWidget {
            background-color: #2b2b2b;
            color: white;
        }
        QLineEdit, QTextEdit {
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