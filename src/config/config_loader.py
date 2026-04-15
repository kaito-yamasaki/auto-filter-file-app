import json
from pathlib import Path

def load_config():
    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / "rules.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
