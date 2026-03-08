"""FIFO queue for actions in the exploration agent."""

from __future__ import annotations

from collections import deque
from typing import Any, Dict, Optional


class ActionQueue:
    """Queue of actions to be executed by the exploration agent."""

    def __init__(self) -> None:
        self.queue: deque[Dict[str, Any]] = deque()

    def add(self, action: Dict[str, Any]) -> None:
        self.queue.append(action)

    def next(self) -> Optional[Dict[str, Any]]:
        if self.queue:
            return self.queue.popleft()
        return None

    def empty(self) -> bool:
        return not self.queue
