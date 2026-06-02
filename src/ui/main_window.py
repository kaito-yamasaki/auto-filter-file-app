from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QFileDialog,
    QTabWidget,
    QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt
import csv
import json
import os
from application.rule import Rule
from config.config_loader import get_config_path


class DropArea(QLabel):
    def __init__(self, on_files_dropped, parent=None):
        super().__init__(parent)
        self.on_files_dropped = on_files_dropped
        self.setAcceptDrops(True)
        self.setObjectName("dropArea")
        self.setText("ここにファイルをドラッグ＆ドロップ")
        self.setMinimumHeight(160)
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
    HISTORY_HEADERS = ["日時", "結果", "ファイル名", "移動先（ルール）", "ユーザー名", "備考"]

    def __init__(self, sorter, config):
        super().__init__()
        self.sorter = sorter
        self.config = config
        self.log_dir = config.get("log_dir", "logs")
        self.log_file = config.get("log_file", "sort_log.csv")
        self.log_path = os.path.join(self.log_dir, self.log_file)
        self.config_path = get_config_path()
        self.history_limit = int(self.config.get("history_limit", 100) or 100)
        self.history_filters = {}
        self.history_all_rows = []
        self.history_sort_column = 0
        self.history_sort_order = Qt.SortOrder.DescendingOrder

        self.setWindowTitle("Auto File Sorter")
        self.setGeometry(200, 200, 900, 500)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.build_main_tabs())

        self.setLayout(main_layout)

        self.setStyleSheet(self.dark_theme())
        self.sync_rule_engine()
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
        left.addWidget(self.drop_area, 2)

        left.addWidget(QLabel("保存先ルート"))
        root_path = self.config.get("root", self.config.get("project_root", ""))
        self.root_input = QLineEdit(root_path)
        self.root_input.editingFinished.connect(self.save_root_path)
        btn_root = QPushButton("参照")
        btn_root.clicked.connect(self.select_root_folder)

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
        self.rule_list.setMinimumHeight(320)
        right.addWidget(self.rule_list, 1)

        self.refresh_rules()

        # 全体のレイアウト
        layout = QHBoxLayout()
        layout.addLayout(left, 3)
        layout.addLayout(right, 5)
        tab.setLayout(layout)

        return tab

    def build_visualization_tab(self):
        tab = QWidget()
        main = QVBoxLayout()

        controls = QHBoxLayout()
        btn_refresh = QPushButton("表示を更新")
        btn_refresh.clicked.connect(self.refresh_visualization)
        controls.addWidget(btn_refresh)

        controls.addWidget(QLabel("履歴件数"))
        self.history_limit_input = QLineEdit(str(self.history_limit))
        self.history_limit_input.setMaximumWidth(80)
        btn_apply_limit = QPushButton("件数適用")
        btn_apply_limit.clicked.connect(self.apply_history_limit)
        controls.addWidget(self.history_limit_input)
        controls.addWidget(btn_apply_limit)

        self.filter_status_label = QLabel("フィルター: なし")
        controls.addWidget(self.filter_status_label)

        btn_filter_popup = QPushButton("フィルター設定")
        btn_filter_popup.clicked.connect(self.open_history_filter_popup_for_current_sort)
        controls.addWidget(btn_filter_popup)

        btn_clear_filter = QPushButton("フィルター解除")
        btn_clear_filter.clicked.connect(self.clear_history_filter)
        controls.addWidget(btn_clear_filter)

        controls.addStretch()
        main.addLayout(controls)

        content = QHBoxLayout()

        left = QVBoxLayout()
        left.addWidget(QLabel("現在のフォルダ構成"))
        self.directory_tree = QTreeWidget()
        self.directory_tree.setHeaderLabels(["フォルダ / ファイル"])
        self.directory_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.directory_tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        left.addWidget(self.directory_tree, 1)

        right = QVBoxLayout()
        self.move_history_title_label = QLabel()
        self.update_history_title_label()
        right.addWidget(self.move_history_title_label)
        self.move_history_table = QTableWidget()
        self.move_history_table.setColumnCount(6)
        self.move_history_table.setHorizontalHeaderLabels(self.HISTORY_HEADERS)
        self.move_history_table.setSortingEnabled(True)
        self.move_history_table.horizontalHeader().setSectionsMovable(True)
        self.move_history_table.horizontalHeader().setSortIndicatorShown(True)
        self.move_history_table.horizontalHeader().setSortIndicator(
            self.history_sort_column,
            self.history_sort_order,
        )
        self.move_history_table.horizontalHeader().sortIndicatorChanged.connect(self.on_history_sort_changed)
        self.move_history_table.cellClicked.connect(self.open_history_filter_popup_from_cell)
        self.move_history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.move_history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.move_history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.move_history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.move_history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.move_history_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.move_history_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.move_history_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        right.addWidget(self.move_history_table, 1)

        content.addLayout(left, 2)
        content.addLayout(right, 5)
        main.addLayout(content, 1)

        tab.setLayout(main)
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
        self.move_history_table.setSortingEnabled(False)
        self.move_history_table.setRowCount(0)

        if not os.path.exists(self.log_path):
            self.move_history_table.setSortingEnabled(True)
            return

        try:
            with open(self.log_path, "r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                target_statuses = {"MOVED", "FAILED", "UNCLASSIFIED"}
                moved_rows = [row for row in reader if row.get("status") in target_statuses]
        except OSError:
            self.move_history_table.setSortingEnabled(True)
            return

        self.history_all_rows = moved_rows
        filtered_rows = self.filter_history_rows(moved_rows)
        recent_rows = filtered_rows[-self.history_limit:]
        recent_rows.reverse()

        self.move_history_table.setRowCount(len(recent_rows))
        for row_index, row in enumerate(recent_rows):
            self.move_history_table.setItem(row_index, 0, QTableWidgetItem(row.get("datetime", "")))
            self.move_history_table.setItem(row_index, 1, QTableWidgetItem(row.get("status", "")))
            self.move_history_table.setItem(row_index, 2, QTableWidgetItem(row.get("filename", "")))
            self.move_history_table.setItem(row_index, 3, QTableWidgetItem(row.get("destination_folder", "")))
            self.move_history_table.setItem(row_index, 4, QTableWidgetItem(row.get("user", "")))
            self.move_history_table.setItem(row_index, 5, QTableWidgetItem(row.get("note", "")))

        self.update_filter_status_label()
        self.move_history_table.setSortingEnabled(True)
        self.move_history_table.sortItems(self.history_sort_column, self.history_sort_order)

    def filter_history_rows(self, rows):
        if not self.history_filters:
            return rows

        key_by_column = {
            0: "datetime",
            1: "status",
            2: "filename",
            3: "destination_folder",
            4: "user",
            5: "note",
        }
        filtered = []
        for row in rows:
            matched = True
            for column, values in self.history_filters.items():
                key = key_by_column.get(column)
                if not key:
                    continue

                row_value = str(row.get(key, ""))
                normalized_row_value = row_value.casefold()
                normalized_targets = {str(v).casefold() for v in values}
                if normalized_row_value not in normalized_targets:
                    matched = False
                    break

            if matched:
                filtered.append(row)

        return filtered

    def apply_history_limit(self):
        text = self.history_limit_input.text().strip()
        try:
            value = int(text)
        except ValueError:
            self.append_message("⚠ 履歴件数は整数で入力してください")
            self.history_limit_input.setText(str(self.history_limit))
            return

        if value <= 0:
            self.append_message("⚠ 履歴件数は1以上で入力してください")
            self.history_limit_input.setText(str(self.history_limit))
            return

        self.history_limit = value
        self.config["history_limit"] = value
        self.update_history_title_label()
        self.save_config_file()
        self.refresh_move_history()
        self.append_message(f"履歴件数を更新: {value}")

    def update_history_title_label(self):
        if hasattr(self, "move_history_title_label"):
            self.move_history_title_label.setText(f"移動履歴（最新{self.history_limit}件）")

    def on_history_sort_changed(self, column, order):
        self.history_sort_column = column
        self.history_sort_order = order

    def open_history_filter_popup_from_cell(self, row, column):
        item = self.move_history_table.item(row, column)
        preselect_value = ""
        if item:
            preselect_value = item.text().strip()

        self.open_history_filter_popup(column, preselect_value)

    def open_history_filter_popup_for_current_sort(self):
        self.open_history_filter_popup(self.history_sort_column)

    def open_history_filter_popup(self, column, preselect_value=""):
        key_by_column = {
            0: "datetime",
            1: "status",
            2: "filename",
            3: "destination_folder",
            4: "user",
            5: "note",
        }
        key = key_by_column.get(column)
        if key is None:
            return

        values = sorted({str(row.get(key, "")) for row in self.history_all_rows})

        dialog = QDialog(self)
        dialog.setWindowTitle(f"フィルター設定: {self.HISTORY_HEADERS[column]}")
        dialog.resize(520, 420)

        layout = QVBoxLayout(dialog)
        info = QLabel("チェックした項目だけ表示します")
        layout.addWidget(info)

        value_list = QListWidget()
        current_selected = set(self.history_filters.get(column, set()))
        for value in values:
            item = QListWidgetItem(value)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            should_check = False
            if current_selected:
                should_check = value in current_selected
            elif preselect_value:
                should_check = value == preselect_value

            item.setCheckState(Qt.CheckState.Checked if should_check else Qt.CheckState.Unchecked)
            value_list.addItem(item)
        layout.addWidget(value_list, 1)

        controls = QHBoxLayout()
        btn_all = QPushButton("全選択")
        btn_none = QPushButton("全解除")
        btn_clear_column = QPushButton("この列のフィルター解除")
        controls.addWidget(btn_all)
        controls.addWidget(btn_none)
        controls.addWidget(btn_clear_column)
        controls.addStretch()
        layout.addLayout(controls)

        actions = QHBoxLayout()
        btn_cancel = QPushButton("キャンセル")
        btn_apply = QPushButton("適用")
        actions.addStretch()
        actions.addWidget(btn_cancel)
        actions.addWidget(btn_apply)
        layout.addLayout(actions)

        def set_all_checked(state):
            for index in range(value_list.count()):
                target_item = value_list.item(index)
                target_item.setCheckState(state)

        def clear_column_filter():
            self.history_filters.pop(column, None)
            self.refresh_move_history()
            self.append_message(f"履歴フィルター解除: {self.HISTORY_HEADERS[column]}")
            dialog.accept()

        def apply_filter():
            selected_values = set()
            for index in range(value_list.count()):
                target_item = value_list.item(index)
                if target_item.checkState() == Qt.CheckState.Checked:
                    selected_values.add(target_item.text())

            if selected_values:
                self.history_filters[column] = selected_values
                self.append_message(f"履歴フィルター適用: {self.HISTORY_HEADERS[column]} ({len(selected_values)}件)")
            else:
                self.history_filters.pop(column, None)
                self.append_message(f"履歴フィルター解除: {self.HISTORY_HEADERS[column]}")

            self.refresh_move_history()
            dialog.accept()

        btn_all.clicked.connect(lambda: set_all_checked(Qt.CheckState.Checked))
        btn_none.clicked.connect(lambda: set_all_checked(Qt.CheckState.Unchecked))
        btn_clear_column.clicked.connect(clear_column_filter)
        btn_cancel.clicked.connect(dialog.reject)
        btn_apply.clicked.connect(apply_filter)

        dialog.exec()

    def clear_history_filter(self):
        self.history_filters = {}
        self.refresh_move_history()
        self.append_message("履歴フィルターを解除")

    def update_filter_status_label(self):
        if not self.history_filters:
            self.filter_status_label.setText("フィルター: なし")
            return

        parts = []
        for column in sorted(self.history_filters.keys()):
            header = self.HISTORY_HEADERS[column]
            count = len(self.history_filters[column])
            parts.append(f"{header}:{count}")

        self.filter_status_label.setText("フィルター: " + " / ".join(parts))

    # ------------------------
    # フォルダ選択
    # ------------------------
    def select_folder(self, field):
        folder = QFileDialog.getExistingDirectory()
        if folder:
            field.setText(folder)

    def select_root_folder(self):
        folder = QFileDialog.getExistingDirectory()
        if not folder:
            return

        self.root_input.setText(folder)
        self.save_root_path()

    def save_root_path(self):
        root_path = self.root_input.text().strip()
        if not root_path:
            return

        if not os.path.isdir(root_path):
            self.show_warning_popup("保存先フォルダが存在しません", f"指定されたフォルダが見つかりません:\n{root_path}")
            self.append_message(f"⚠ 保存先フォルダが存在しません: {root_path}")
            return

        current_root = self.config.get("root", "")
        if current_root == root_path:
            return

        self.config["root"] = root_path
        self.save_config_file()
        self.refresh_visualization()
        self.append_message(f"保存先ルートを更新: {root_path}")

    def sync_rule_engine(self):
        if not hasattr(self.sorter, "rule_engine"):
            return

        rules = [Rule(k, v) for k, v in self.config.get("rules", {}).items()]
        self.sorter.rule_engine.rules = rules
        self.sorter.rule_engine.default_path = self.config.get("default")

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
        self.sync_rule_engine()
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

        key = selected.data(Qt.ItemDataRole.UserRole)
        if not key:
            self.append_message("⚠ 削除対象のキー取得に失敗しました")
            return

        if key not in self.config["rules"]:
            self.append_message(f"⚠ ルールが見つかりません: {key}")
            return

        del self.config["rules"][key]
        self.sync_rule_engine()
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
            item = QListWidgetItem(f"{k} → {v}")
            item.setData(Qt.ItemDataRole.UserRole, k)
            self.rule_list.addItem(item)

    def process_dropped_files(self, file_paths):
        if not file_paths:
            self.append_message("⚠ ドロップされたファイルがありません")
            return

        root_path = self.root_input.text().strip()
        if not root_path or not os.path.isdir(root_path):
            self.show_warning_popup("保存先フォルダが存在しません", f"参照先フォルダを確認してください:\n{root_path or '(未設定)'}")
            self.append_message(f"⚠ 参照先フォルダが存在しません: {root_path or '(未設定)'}")
            return

        if hasattr(self.sorter, "file_repo"):
            self.sorter.file_repo.root_path = root_path

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

    def show_warning_popup(self, title, message):
        QMessageBox.warning(self, title, message)

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