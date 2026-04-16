import json
import shutil
import sys
from pathlib import Path


def get_config_path():
    candidates = []

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / "rules.json")

        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "rules.json")

    project_root = Path(__file__).resolve().parents[2]
    candidates.append(project_root / "rules.json")

    for path in candidates:
        if path.exists():
            return path

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled_path = Path(meipass) / "rules.json"
            writable_path = exe_dir / "rules.json"
            if bundled_path.exists():
                shutil.copy2(bundled_path, writable_path)
                return writable_path

    return project_root / "rules.json"


def load_config():
    config_path = get_config_path()

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
