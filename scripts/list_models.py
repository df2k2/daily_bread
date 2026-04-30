from __future__ import annotations

import sys

from .gemini_client import get_client


def main() -> int:
    client = get_client()
    rows: list[tuple[str, str]] = []
    for m in client.models.list():
        methods = list(getattr(m, "supported_actions", []) or [])
        if not methods:
            methods = list(getattr(m, "supported_generation_methods", []) or [])
        if methods and "generateContent" not in methods:
            continue
        rows.append((m.name, ", ".join(methods) or "-"))
    rows.sort()
    width = max(len(n) for n, _ in rows) if rows else 0
    for name, methods in rows:
        print(f"{name:<{width}}  {methods}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
