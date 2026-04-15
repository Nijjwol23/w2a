"""
W2A LangChain Integration

Turns any W2A-enabled site's skills into LangChain tools.

Usage:
    from w2a.integrations.langchain import W2ATool

    tools = await W2ATool.from_url("stripe.com")
    # Each skill becomes a structured LangChain tool

    # Or with a pre-discovered site:
    from w2a import discover
    site = await discover("w2a-protocol.org")
    tools = W2ATool.from_site(site)

    # Use with any LangChain agent:
    from langchain.agents import initialize_agent, AgentType
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="gpt-4")
    agent = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS)
    agent.run("validate my agents.json file")
"""

import json
from typing import Any, Dict, List, Optional, Type

from w2a.client import W2AClient, discover
from w2a.models import W2ASite, W2ASkill

try:
    from langchain.tools import BaseTool
    from langchain.callbacks.manager import CallbackManagerForToolRun
    from pydantic import BaseModel, Field, create_model
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseTool = object
    BaseModel = object


def _w2a_type_to_python(type_str: str) -> Any:
    """Map W2A type strings to Python type annotations."""
    mapping = {
        "string": str,
        "string?": Optional[str],
        "int": int,
        "int?": Optional[int],
        "float": float,
        "float?": Optional[float],
        "bool": bool,
        "bool?": Optional[bool],
        "object": Dict[str, Any],
        "object?": Optional[Dict[str, Any]],
        "string[]": List[str],
        "int[]": List[int],
        "object[]": List[Dict[str, Any]],
    }
    return mapping.get(type_str, Any)


def _build_input_schema(skill: W2ASkill) -> Type:
    """Dynamically build a Pydantic input schema from W2A skill inputs."""
    if not LANGCHAIN_AVAILABLE:
        raise ImportError(
            "langchain and pydantic are required. "
            "Install with: pip install w2a[langchain]"
        )

    fields = {}
    for field_name, field_type in skill.input.items():
        python_type = _w2a_type_to_python(field_type)
        is_optional = field_type.endswith("?")
        if is_optional:
            fields[field_name] = (
                python_type,
                Field(default=None, description=f"{field_name} ({field_type})")
            )
        else:
            fields[field_name] = (
                python_type,
                Field(..., description=f"{field_name} ({field_type})")
            )

    if not fields:
        fields["_placeholder"] = (
            Optional[str],
            Field(default=None, description="No input required")
        )

    return create_model(
        f"{skill.id}_input",
        **fields,
    )


class W2ASkillTool(BaseTool):
    """
    A LangChain tool wrapping a single W2A skill.

    Created automatically by W2ATool.from_url() or W2ATool.from_site().
    You typically don't instantiate this directly.
    """

    name: str
    description: str
    skill: Any  # W2ASkill — typed as Any to avoid pydantic conflict
    site: Any   # W2ASite
    return_direct: bool = False

    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs,
    ) -> str:
        """Sync execution — runs the async version via asyncio."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self._arun(**kwargs))
                    return future.result()
            else:
                return loop.run_until_complete(self._arun(**kwargs))
        except Exception as e:
            return f"Error calling {self.skill.id}: {str(e)}"

    async def _arun(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs,
    ) -> str:
        """Async execution of the W2A skill."""
        async with W2AClient() as client:
            result = await client.call(self.site, self.skill.id, **kwargs)
            return json.dumps(result, indent=2)

    class Config:
        arbitrary_types_allowed = True


class W2ATool:
    """
    Factory for creating LangChain tools from a W2A-enabled site.

    Each skill in the site's agents.json becomes a separate tool
    with a typed input schema built from the skill's declared inputs.
    """

    @classmethod
    async def from_url(
        cls,
        url: str,
        include_auth_required: bool = False,
        skill_ids: Optional[List[str]] = None,
    ) -> List[W2ASkillTool]:
        """
        Discover a site and return its skills as LangChain tools.

        Args:
            url: Site URL or domain.
            include_auth_required: If False (default), only include
                                   skills with auth="none". Set to True
                                   to include all skills (you'll need
                                   to handle auth yourself).
            skill_ids: Optional list of specific skill ids to include.
                       If None, all matching skills are included.

        Returns:
            List of LangChain BaseTool instances, one per skill.

        Example:
            tools = await W2ATool.from_url("w2a-protocol.org")
            # tools is a list of BaseTool ready for LangChain agents
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "langchain and pydantic are required. "
                "Install with: pip install w2a[langchain]"
            )

        site = await discover(url)
        return cls.from_site(
            site,
            include_auth_required=include_auth_required,
            skill_ids=skill_ids,
        )

    @classmethod
    def from_site(
        cls,
        site: W2ASite,
        include_auth_required: bool = False,
        skill_ids: Optional[List[str]] = None,
    ) -> List[W2ASkillTool]:
        """
        Convert a pre-discovered W2ASite into LangChain tools.

        Args:
            site: A W2ASite returned by discover().
            include_auth_required: Include skills that require auth.
            skill_ids: Specific skill ids to include.

        Returns:
            List of W2ASkillTool instances.
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "langchain and pydantic are required. "
                "Install with: pip install w2a[langchain]"
            )

        skills = site.skills

        if not include_auth_required:
            skills = [s for s in skills if s.auth == "none"]

        if skill_ids:
            skills = [s for s in skills if s.id in skill_ids]

        tools = []
        for skill in skills:
            input_schema = _build_input_schema(skill)

            tool = W2ASkillTool(
                name=f"w2a_{skill.id}",
                description=(
                    f"{skill.intent}. "
                    f"Calls {skill.action} on {site.name}."
                ),
                skill=skill,
                site=site,
                args_schema=input_schema,
            )
            tools.append(tool)

        return tools
