import os

MODEL_NAME = os.getenv("UI_BUG_MODEL", "ui-bug-detector")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
TIMEOUT_MS = int(os.getenv("BROWSER_TIMEOUT_MS", "30000"))
WAIT_AFTER_LOAD_MS = int(os.getenv("WAIT_AFTER_LOAD_MS", "1500"))

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 390, "height": 844},
}

MAX_MODEL_TEXT_CHARS = 24000
MAX_ITEMS_PER_DIAGNOSTIC = 40
