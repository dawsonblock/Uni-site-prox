"""Track visited states and executed actions to avoid loops."""

from __future__ import annotations

import hashlib
from typing import Dict, Any


class StateTracker:
    """Prevent revisiting the same DOM or executing the same action twice."""

    def __init__(self) -> None:
        self.visited_states: set[str] = set()
        self.executed_actions: set[str] = set()

    def fingerprint_dom(self, html: str) -> str:
        return hashlib.sha256(html.encode()).hexdigest()

    def seen_state(self, html: str) -> bool:
        fp = self.fingerprint_dom(html)
        if fp in self.visited_states:
            return True
        self.visited_states.add(fp)
        return False

    def seen_action(self, action: Dict[str, Any]) -> bool:
        key = str(action)
        if key in self.executed_actions:
            return True
        self.executed_actions.add(key)
        return False
