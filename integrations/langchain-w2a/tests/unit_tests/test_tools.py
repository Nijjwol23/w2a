"""
Standard unit tests for langchain-w2a tools.

Follows LangChain's standard test pattern from langchain-tests.
Run with: pytest tests/unit_tests/

These tests verify our tools conform to LangChain's BaseTool interface
without requiring any network calls or external services.
"""

from typing import Type
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_tests.unit_tests import ToolsUnitTests

from langchain_w2a import W2ADiscoverTool, W2ASkillTool


class TestW2ADiscoverToolUnit(ToolsUnitTests):
    """Standard LangChain unit tests for W2ADiscoverTool."""

    @property
    def tool_constructor(self) -> Type[W2ADiscoverTool]:
        return W2ADiscoverTool

    @property
    def tool_constructor_params(self) -> dict:
        return {}

    @property
    def tool_invoke_params_example(self) -> dict:
        """Parameters to pass to the tool's invoke method during testing."""
        return {"url": "w2a-protocol.org"}


class TestW2ASkillToolUnit(ToolsUnitTests):
    """Standard LangChain unit tests for W2ASkillTool."""

    @property
    def tool_constructor(self) -> Type[W2ASkillTool]:
        return W2ASkillTool

    @property
    def tool_constructor_params(self) -> dict:
        return {}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {
            "url": "w2a-protocol.org",
            "skill_id": "check_site",
            "params": {"url": "stripe.com"},
        }


# ── Additional package-specific unit tests ────────────────────────────────────


class TestW2ADiscoverToolBehavior:
    """Behavior-specific tests for W2ADiscoverTool that don't fit the standard suite."""

    def test_tool_has_name(self):
        tool = W2ADiscoverTool()
        assert tool.name == "w2a_discover"

    def test_tool_has_description(self):
        tool = W2ADiscoverTool()
        assert tool.description
        assert "W2A" in tool.description

    def test_args_schema_has_url(self):
        tool = W2ADiscoverTool()
        schema = tool.args_schema.model_json_schema()
        assert "url" in schema["properties"]
        assert schema["properties"]["url"]["type"] == "string"

    def test_tool_is_basetool(self):
        from langchain_core.tools import BaseTool
        tool = W2ADiscoverTool()
        assert isinstance(tool, BaseTool)


class TestW2ASkillToolBehavior:
    """Behavior-specific tests for W2ASkillTool."""

    def test_tool_has_name(self):
        tool = W2ASkillTool()
        assert tool.name == "w2a_call_skill"

    def test_tool_has_description(self):
        tool = W2ASkillTool()
        assert tool.description
        assert "skill" in tool.description.lower()

    def test_args_schema_has_required_fields(self):
        tool = W2ASkillTool()
        schema = tool.args_schema.model_json_schema()
        assert "url" in schema["properties"]
        assert "skill_id" in schema["properties"]
        assert "params" in schema["properties"]


class TestW2AToolkitBehavior:
    """Test W2AToolkit construction and tool generation."""

    def test_import(self):
        from langchain_w2a import W2AToolkit
        assert W2AToolkit is not None

    def test_toolkit_is_basetoolkit(self):
        from langchain_core.tools import BaseToolkit
        from langchain_w2a import W2AToolkit
        # Class-level check — instantiation requires async discovery
        assert issubclass(W2AToolkit, BaseToolkit)
