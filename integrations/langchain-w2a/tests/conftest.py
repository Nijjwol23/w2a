"""Pytest configuration for langchain-w2a tests."""

import pytest


def pytest_collection_modifyitems(config, items):
    """Mark async tests automatically."""
    for item in items:
        if "asyncio" in item.keywords or "async def" in str(item.function):
            item.add_marker(pytest.mark.asyncio)
