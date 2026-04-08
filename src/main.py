import sys
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from application.file_sorter import FileSorter
from application.rule_engine import RuleEngine
from application.rule import Rule
from infra.file_repository import FileRepository
from infra.logger import Logger
from config.config_loader import load_config

if __name__ == "__main__":
    config = load_config()

    rules = [Rule(k, v) for k, v in config["rules"].items()]
    rule_engine = RuleEngine(rules, config.get("default"))

    file_repo = FileRepository(config["root"])
    logger = Logger()

    sorter = FileSorter(rule_engine, file_repo, logger)

    app = QApplication(sys.argv)
    window = MainWindow(sorter, config)
    window.show()
    sys.exit(app.exec())