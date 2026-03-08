"""DOM inspector used by the exploration agent.

The inspector locates interactive elements on the page such as buttons,
links and text inputs. These are converted into simple action descriptions
that can be queued for execution by the exploration agent. The inspector
does not execute any actions and is safe to call repeatedly.
"""

from __future__ import annotations

from typing import List, Dict
from playwright.async_api import Page


class DOMInspector:
    """Scan a page for potential interactive elements."""

    CLICK_SELECTORS = [
        "a[href]",
        "button",
        "[role='button']",
        "input[type='submit']",
    ]
    INPUT_SELECTORS = [
        "input[type='text']",
        "input[type='search']",
        "textarea",
    ]

    async def scan(self, page: Page) -> List[Dict[str, str]]:
        """Return a list of element descriptors to interact with.

        Each descriptor is a dict with ``type`` (``click`` or ``input``)
        and ``selector`` specifying how to locate the element. For clicks
        optional ``text`` is captured for logging or ranking purposes.
        """
        elements: List[Dict[str, str]] = []
        for selector in self.CLICK_SELECTORS:
            locator = page.locator(selector)
            count = await locator.count()
            for index in range(count):
                node = locator.nth(index)
                try:
                    text = await node.inner_text()
                except Exception:
                    text = ""
                elements.append({
                    "type": "click",
                    "selector": selector,
                    "index": index,
                    "text": text[:50],
                })
        for selector in self.INPUT_SELECTORS:
            locator = page.locator(selector)
            count = await locator.count()
            for index in range(count):
                elements.append({
                    "type": "input",
                    "selector": selector,
                    "index": index,
                })
        return elements
