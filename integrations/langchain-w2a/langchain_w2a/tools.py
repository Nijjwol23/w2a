"""
W2A LangChain Tools

Two tool types:
- W2ADiscoverTool: discover what a W2A-enabled site can do
- W2ASkillTool: call a specific skill on a W2A-enabled site
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class W2ADiscoverInput(BaseModel):
    """Input for W2ADiscoverTool."""
    url: str = Field(
        description="The website URL or domain to check for W2A support. "
                    "Examples: 'stripe.com', 'https://myshop.com'"
    )


class W2ADiscoverTool(BaseTool):
    """
    Discover what a W2A-enabled website can do.

    Fetches the site's /.well-known/agents.json manifest and returns
    a structured summary of its declared skills and capabilities.

    Use this when you need to understand what a website offers before
    deciding which skill to call.
    """

    name: str = "w2a_discover"
    description: str = (
        "Discover what a W2A-enabled website can do. "
        "Returns the site's declared skills, actions, and access policies. "
        "Use this before calling a specific skill to understand what's available."
    )
    args_schema: Type[BaseModel] = W2ADiscoverInput
    return_direct: bool = False

    def _run(
        self,
        url: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        return asyncio.run(self._arun(url, run_manager=run_manager))

    async def _arun(
        self,
        url: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        try:
            from w2a import discover
            from w2a.exceptions import ManifestNotFound
        except ImportError:
            return (
                "The 'w2a' package is required. Install with: pip install w2a"
            )

        try:
            site = await discover(url)
        except ManifestNotFound:
            return (
                f"{url} has not adopted the W2A protocol yet — "
                f"no /.well-known/agents.json found. "
                f"Generate one at https://w2a-protocol.org/tools"
            )
        except Exception as e:
            return f"Error discovering {url}: {str(e)}"

        result = {
            "name": site.name,
            "type": site.type,
            "url": site.origin,
            "a2a_compatible": site.a2aCompatible if hasattr(site, 'a2aCompatible') else site.a2a_compatible,
            "skills": [
                {
                    "id": s.id,
                    "intent": s.intent,
                    "action": s.action,
                    "auth": s.auth,
                    "input": s.input,
                }
                for s in site.skills
            ],
            "policy": {
                "rate_limit": site.policy.rate_limit if site.policy else None,
                "open": site.policy.is_open if site.policy else True,
            } if site.policy else None,
        }

        return json.dumps(result, indent=2)


class W2ACallInput(BaseModel):
    """Input for W2ASkillTool."""
    url: str = Field(
        description="The website URL or domain. Example: 'w2a-protocol.org'"
    )
    skill_id: str = Field(
        description="The id of the skill to call, as declared in the site's agents.json. "
                    "Use w2a_discover first to see available skill ids."
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters for the skill, matching its declared input schema. "
                    "Pass as a JSON object. Example: {\"q\": \"running shoes\", \"limit\": 10}"
    )


class W2ASkillTool(BaseTool):
    """
    Call a specific skill on a W2A-enabled website.

    Discovers the site's agents.json, finds the requested skill,
    and executes the corresponding HTTP call with the provided parameters.

    Use w2a_discover first to find available skill ids and their input schemas.
    """

    name: str = "w2a_call_skill"
    description: str = (
        "Call a specific skill (action) on a W2A-enabled website. "
        "Provide the site URL, the skill id (from w2a_discover), and any parameters. "
        "Returns the JSON response from the skill endpoint."
    )
    args_schema: Type[BaseModel] = W2ACallInput
    return_direct: bool = False

    def _run(
        self,
        url: str,
        skill_id: str,
        params: Optional[Dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        return asyncio.run(
            self._arun(url, skill_id, params=params, run_manager=run_manager)
        )

    async def _arun(
        self,
        url: str,
        skill_id: str,
        params: Optional[Dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        try:
            from w2a import W2AClient
            from w2a.exceptions import ManifestNotFound, SkillNotFound, SkillCallError
        except ImportError:
            return "The 'w2a' package is required. Install with: pip install w2a"

        async with W2AClient() as client:
            try:
                site = await client.discover(url)
            except ManifestNotFound:
                return (
                    f"{url} has not adopted W2A yet. "
                    f"No /.well-known/agents.json found."
                )
            except Exception as e:
                return f"Error connecting to {url}: {str(e)}"

            try:
                result = await client.call(site, skill_id, **(params or {}))
                return json.dumps(result, indent=2)
            except SkillNotFound as e:
                return str(e)
            except SkillCallError as e:
                return f"Skill call failed: {str(e)}"
            except Exception as e:
                return f"Error calling skill '{skill_id}': {str(e)}"
