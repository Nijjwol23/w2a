"""
W2AToolkit — creates a set of LangChain tools for a specific W2A-enabled site.

Instead of generic discover/call tools, the toolkit creates one dedicated tool
per skill — with the site URL pre-bound and a typed input schema built from
the skill's declared inputs.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool, BaseToolkit
from pydantic import BaseModel, ConfigDict, Field, create_model


from langchain_w2a.tools import W2ADiscoverTool, W2ASkillTool


def _w2a_type_to_field(type_str: str):
    """Map W2A type string to a Pydantic field definition."""
    is_optional = type_str.endswith("?")
    base = type_str.rstrip("?")

    type_map = {
        "string": str,
        "int": int,
        "float": float,
        "bool": bool,
        "object": Dict[str, Any],
        "string[]": List[str],
        "int[]": List[int],
        "object[]": List[Dict[str, Any]],
    }
    python_type = type_map.get(base, str)

    if is_optional:
        return (Optional[python_type], Field(default=None))
    return (python_type, Field(...))


def _build_schema(skill_id: str, inputs: Dict[str, str]) -> Type[BaseModel]:
    """Dynamically build a Pydantic schema from W2A skill inputs."""
    fields = {}
    for name, type_str in inputs.items():
        python_type, field = _w2a_type_to_field(type_str)
        fields[name] = (python_type, field)

    if not fields:
        return BaseModel

    return create_model(f"{skill_id}_input", **fields)


class W2AToolkit(BaseToolkit):
    """
    A LangChain toolkit for a W2A-enabled website.

    Creates one tool per skill declared in the site's agents.json.
    Each tool has a typed input schema and a description derived from
    the skill's intent field.

    Usage:
        toolkit = await W2AToolkit.from_url("w2a-protocol.org")
        tools = toolkit.get_tools()

        # add to any agent
        agent_executor = AgentExecutor(agent=agent, tools=tools)
    """

    site_url: str
    site_name: str = ""
    _skill_tools: List[BaseTool] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def get_tools(self) -> List[BaseTool]:
        """Return all tools for this site."""
        return list(self._skill_tools) + [
            W2ADiscoverTool(),
            W2ASkillTool(),
        ]

    @classmethod
    async def from_url(
        cls,
        url: str,
        include_auth_required: bool = False,
        skill_ids: Optional[List[str]] = None,
    ) -> "W2AToolkit":
        """
        Create a W2AToolkit for a specific W2A-enabled site.

        Args:
            url: The site URL or domain. e.g. "stripe.com"
            include_auth_required: Include skills that require authentication.
                                   Default False — only public skills.
            skill_ids: Specific skill ids to include. None = all matching skills.

        Returns:
            W2AToolkit with one tool per skill.

        Raises:
            ImportError: If the 'w2a' package is not installed.
            ManifestNotFound: If the site has no agents.json.

        Example:
            toolkit = await W2AToolkit.from_url("w2a-protocol.org")
            for tool in toolkit.get_tools():
                print(tool.name, "—", tool.description)
        """
        try:
            from w2a import discover
        except ImportError:
            raise ImportError(
                "The 'w2a' package is required. Install with: pip install w2a"
            )

        site = await discover(url)
        skills = site.skills

        if not include_auth_required:
            skills = [s for s in skills if s.auth == "none"]

        if skill_ids:
            skills = [s for s in skills if s.id in skill_ids]

        skill_tools = []
        for skill in skills:
            schema = _build_schema(skill.id, skill.input or {})
            bound_url = site.origin
            bound_skill_id = skill.id

            # Build a dedicated tool class for this skill
            class _BoundSkillTool(BaseTool):
                name: str = f"{site.name.lower().replace(' ', '_')}_{skill.id}"
                description: str = (
                    f"{skill.intent}. "
                    f"Calls {skill.action} on {site.name}."
                )
                args_schema: Type[BaseModel] = schema
                _url: str = bound_url
                _skill_id: str = bound_skill_id

                def _run(
                    self,
                    run_manager: Optional[CallbackManagerForToolRun] = None,
                    **kwargs,
                ) -> str:
                    return asyncio.run(self._arun(run_manager=run_manager, **kwargs))

                async def _arun(
                    self,
                    run_manager: Optional[CallbackManagerForToolRun] = None,
                    **kwargs,
                ) -> str:
                    from w2a import W2AClient
                    async with W2AClient() as client:
                        site_obj = await client.discover(self._url)
                        result = await client.call(
                            site_obj, self._skill_id, **kwargs
                        )
                        return json.dumps(result, indent=2)

                model_config = ConfigDict(arbitrary_types_allowed=True)

            skill_tools.append(_BoundSkillTool())

        toolkit = cls(site_url=site.origin, site_name=site.name)
        toolkit._skill_tools = skill_tools
        return toolkit

    @classmethod
    def from_url_sync(
        cls,
        url: str,
        include_auth_required: bool = False,
        skill_ids: Optional[List[str]] = None,
    ) -> "W2AToolkit":
        """Synchronous version of from_url() for non-async contexts."""
        return asyncio.run(
            cls.from_url(url, include_auth_required, skill_ids)
        )
