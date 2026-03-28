"""Shared pytest fixtures for the MZI test suite."""
import os
import sys

# Set SDL env vars BEFORE any pygame import to avoid opening real windows/audio.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Ensure the project root is on sys.path so that imports like
# ``from utils.vector import Vector2`` work the same way as when
# running the application from the repo root.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
import pygame


@pytest.fixture(scope="session", autouse=True)
def _init_pygame():
    """Initialize pygame once for the entire test session, then quit."""
    pygame.init()
    # Create a tiny display surface so that Surface/font operations work.
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()
