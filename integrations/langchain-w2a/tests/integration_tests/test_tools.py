"""
Standard integration tests for langchain-w2a.

These tests make real network calls to w2a-protocol.org which serves
a live agents.json. They verify end-to-end behavior including discovery,
skill listing, and skill invocation.

Run with: pytest tests/integration_tests/

Requires internet access. Tests are skipped if the site is unreachable.
"""

import json
from typing import Type

import pytest
from langchain_tests.integration_tests import ToolsIntegrationTests

from langchain_w2a import W2ADiscoverTool, W2ASkillTool


class TestW2ADiscoverToolIntegration(ToolsIntegrationTests):
    """Standard LangChain integration tests for W2ADiscoverTool."""

    @property
    def tool_constructor(self) -> Type[W2ADiscoverTool]:
        return W2ADiscoverTool

    @property
    def tool_constructor_params(self) -> dict:
        return {}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"url": "w2a-protocol.org"}


class TestW2ASkillToolIntegration(ToolsIntegrationTests):
    """Standard LangChain integration tests for W2ASkillTool."""

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


# ── End-to-end integration tests ──────────────────────────────────────────────


class TestW2AEndToEnd:
    """End-to-end tests against the live W2A protocol site."""

    @pytest.mark.asyncio
    async def test_discover_w2a_protocol_org(self):
        """Should successfully discover w2a-protocol.org with 6 skills."""
        tool = W2ADiscoverTool()
        result = await tool._arun("w2a-protocol.org")
        data = json.loads(result)

        assert data["name"]
        assert data["type"] == "api"
        assert "w2a-protocol.org" in data["url"]
        assert len(data["skills"]) >= 5

    @pytest.mark.asyncio
    async def test_discover_non_w2a_site_handled_gracefully(self):
        """Non-W2A sites return a clear message, not a crash."""
        tool = W2ADiscoverTool()
        result = await tool._arun("example.com")

        assert "W2A" in result or "not adopted" in result.lower() or "agents.json" in result.lower()

    @pytest.mark.asyncio
    async def test_call_skill_check_site(self):
        """Should successfully call the check_site skill on w2a-protocol.org."""
        tool = W2ASkillTool()
        result = await tool._arun(
            url="w2a-protocol.org",
            skill_id="check_site",
            params={"url": "example.com"},
        )
        data = json.loads(result)

        # check_site returns a w2a_enabled boolean
        assert "w2a_enabled" in data or "manifest_url" in data

    @pytest.mark.asyncio
    async def test_toolkit_from_url(self):
        """W2AToolkit.from_url should create tools from a real site."""
        from langchain_w2a import W2AToolkit

        toolkit = await W2AToolkit.from_url("w2a-protocol.org")
        tools = toolkit.get_tools()

        # Should have skill-bound tools plus the two generic ones
        assert len(tools) >= 2
        names = [t.name for t in tools]
        assert "w2a_discover" in names
        assert "w2a_call_skill" in names
