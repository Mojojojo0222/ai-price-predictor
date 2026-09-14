"""Pytest fixtures and path configuration for the test suite."""

import sys
from pathlib import Path

# Ensure the project root is importable regardless of CWD
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
