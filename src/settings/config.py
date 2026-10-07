from pathlib import Path

import yaml

project_root = Path(__file__).resolve().parents[2]
file_path = project_root / "config" / "project.yml"


def load_config():
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
    return config
