import json, os
from typing import Dict, List

def ensure(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)

def read(path: str) -> List[Dict]:
    ensure(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def append(path: str, item: Dict) -> bool:
    logs = read(path)
    if item not in logs:
        logs.append(item)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
        return True
    return False
