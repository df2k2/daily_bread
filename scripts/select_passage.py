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


def _record(state: dict, reference: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    state["last_run"] = now
    history = state.get("history", [])
    history.append({"reference": reference, "at": now})
    state["history"] = history[-60:]


def _pick_random(plan: dict, history: list[dict]) -> str:
    recent = {h["reference"] for h in history[-7:]}
    candidates = [p for p in plan["passages"] if p not in recent] or plan["passages"]
    return random.choice(candidates)


def _pick_sequential(plan_name: str, plan: dict, state: dict) -> str:
    key = f"{plan_name}_index"
    idx = state.get(key, 0) % len(plan["passages"])
    state[key] = idx + 1
    return plan["passages"][idx]


def _pick_daily(plan_name: str, plan: dict, slot: str, state: dict) -> str:
    days = plan["days"]
    if not days:
        raise ValueError(f"Plan {plan_name!r} has no days defined.")
    key = f"{plan_name}_day_index"
    idx = state.get(key, 0) % len(days)
    today_block = days[idx]
    readings = today_block.get(slot) or today_block.get("morning") or []
    if not readings:
        raise ValueError(f"Plan {plan_name!r} day {idx} has no {slot} reading.")

    rotation_key = f"{plan_name}_{slot}_rot"
    rot = state.get(rotation_key, 0) % len(readings)
    state[rotation_key] = rot + 1

    if slot == "evening":
        state[key] = idx + 1

    return readings[rot]


def select_passage(plan_name: str, slot: str = "morning") -> str:
    with READING_PLAN_PATH.open() as f:
        plans = json.load(f)
    if plan_name not in plans:
        raise ValueError(f"Unknown reading plan: {plan_name}")

    plan = plans[plan_name]
    state = load_state()
    history = state.get("history", [])

    plan_type = plan.get("type", "random")
    if plan_type == "random":
        reference = _pick_random(plan, history)
    elif plan_type == "sequential":
        reference = _pick_sequential(plan_name, plan, state)
    elif plan_type == "daily":
        reference = _pick_daily(plan_name, plan, slot, state)
    else:
        raise ValueError(f"Unknown plan type: {plan_type!r}")

    _record(state, reference)
    save_state(state)
    return reference
