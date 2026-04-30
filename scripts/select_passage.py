from __future__ import annotations

import json
import random
from datetime import datetime, timezone

from .config import READING_PLAN_PATH, STATE_PATH


def load_state() -> dict:
    with STATE_PATH.open() as f:
        return json.load(f)


def save_state(state: dict) -> None:
    with STATE_PATH.open("w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def select_passage(plan_name: str) -> str:
    with READING_PLAN_PATH.open() as f:
        plans = json.load(f)
    if plan_name not in plans:
        raise ValueError(f"Unknown reading plan: {plan_name}")

    state = load_state()
    history = state.get("history", [])

    if plan_name == "random":
        recent = {h["reference"] for h in history[-7:]}
        candidates = [p for p in plans[plan_name] if p not in recent] or plans[plan_name]
        reference = random.choice(candidates)
    else:
        idx = state.get(f"{plan_name}_index", 0) % len(plans[plan_name])
        reference = plans[plan_name][idx]
        state[f"{plan_name}_index"] = idx + 1

    state["last_run"] = datetime.now(timezone.utc).isoformat()
    history.append({"reference": reference, "at": state["last_run"]})
    state["history"] = history[-60:]
    save_state(state)
    return reference
