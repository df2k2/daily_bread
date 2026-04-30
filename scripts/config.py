from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yml"
DATA_DIR = ROOT / "data"
CONTENT_DIR = ROOT / "content"
PROMPTS_DIR = ROOT / "prompts"
STATE_PATH = DATA_DIR / "state.json"
READING_PLAN_PATH = DATA_DIR / "reading_plan.json"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)
