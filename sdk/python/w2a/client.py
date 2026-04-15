"""
W2A Client — discover and interact with W2A-enabled websites.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .exceptions import ManifestInvalid, ManifestNotFound, SkillCallError, SkillNotFound
from .models import W2APolicy, W2ASite, W2ASkill

# W2A validator endpoint — used for manifest validation
W2A_VALIDATOR = "https://w2a-protocol.org/api/validate"

# Request headers sent with all W2A discovery requests
W2A_HEADERS = {
    "Accept": "application/json",
    "Agent-W2A": "1.0",
    "User-Agent": "W2A-Python-SDK/0.1.0 (+https://w2a-protocol.org)",
}


def _normalise_url(url: str) -> str:
    """Ensure URL has a scheme and return the origin."""
    if not url.startswith("http"):
        url = "https://" + url
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _parse_skill(raw: Dict[str, Any]) -> W2ASkill:
    return W2ASkill(
        id=raw.get("id", ""),
        intent=raw.get("intent", ""),
        action=raw.get("action", "GET /"),
        auth=raw.get("auth", "none"),
        input=raw.get("input", {}),
        output=raw.get("output", {}),
        description=raw.get("description"),
    )


def _parse_manifest(origin: str, manifest: Dict[str, Any]) -> W2ASite:
    site_data = manifest.get("site", {})
    skills_raw = manifest.get("skills", manifest.get("capabilities", []))
    policy_raw = manifest.get("policies", {})

    policy = W2APolicy(
        rate_limit=policy_raw.get("rate_limit"),
        allowed_agents=policy_raw.get("allowed_agents", ["*"]),
        blocked_agents=policy_raw.get("blocked_agents", []),
        require_identity=policy_raw.get("require_identity", False),
    )

    return W2ASite(
        name=site_data.get("name", origin),
        type=site_data.get("type", "other"),
        origin=origin,
        manifest_url=f"{origin}/.well-known/agents.json",
        language=site_data.get("language", "en"),
        description=site_data.get("description"),
        skills=[_parse_skill(s) for s in skills_raw],
        policy=policy,
        a2a_compatible=bool(manifest.get("a2a_profile")),
        w2a_version=manifest.get("w2a", "1.0"),
        _raw=manifest,
    )


class W2AClient:
    """
    Async client for discovering and interacting with W2A-enabled websites.

    Usage:
        async with W2AClient() as client:
            site = await client.discover("stripe.com")
            result = await client.call(site, "search_products", q="shoes")

    Or use the module-level shortcut:
        site = await discover("stripe.com")
    """

    def __init__(
        self,
        timeout: int = 10,
        validate: bool = False,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Args:
            timeout: Request timeout in seconds.
            validate: If True, validate the manifest against the W2A spec
                      before returning. Adds a network round-trip.
            headers: Additional headers to include in all requests.
        """
        self.timeout = timeout
        self.validate = validate
        self._extra_headers = headers or {}
        self._session = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None

    async def _get_session(self):
        try:
            import aiohttp
        except ImportError:
            raise ImportError(
                "aiohttp is required for async W2A discovery. "
                "Install it with: pip install w2a[async]"
            )
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={**W2A_HEADERS, **self._extra_headers},
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )
        return self._session

    async def discover(self, url: str) -> W2ASite:
        """
        Discover a W2A-enabled site and return its capabilities.

        Args:
            url: The site URL or domain. e.g. "stripe.com" or
                 "https://stripe.com"

        Returns:
            W2ASite with skills, policies, and metadata.

        Raises:
            ManifestNotFound: If the site has no agents.json.
            ManifestInvalid: If the manifest fails validation.

        Example:
            site = await client.discover("petstore.swagger.io")
            print(f"{site.name} has {len(site.skills)} skills")
            for skill in site.public_skills:
                print(f"  {skill.id}: {skill.intent}")
        """
        origin = _normalise_url(url)
        manifest_url = f"{origin}/.well-known/agents.json"

        session = await self._get_session()

        try:
            async with session.get(manifest_url) as resp:
                if resp.status == 404:
                    raise ManifestNotFound(origin)
                if resp.status != 200:
                    raise ManifestNotFound(origin)
                try:
                    manifest = await resp.json(content_type=None)
                except (json.JSONDecodeError, Exception):
                    raise ManifestNotFound(origin)
        except ManifestNotFound:
            raise
        except Exception as e:
            raise ManifestNotFound(origin) from e

        if self.validate:
            await self._validate(manifest, origin)

        return _parse_manifest(origin, manifest)

    async def _validate(self, manifest: Dict, origin: str):
        """Validate manifest against the W2A spec API."""
        try:
            session = await self._get_session()
            async with session.post(
                W2A_VALIDATOR,
                json={"manifest": manifest},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if not data.get("valid"):
                        from .models import W2AError
                        errors = [
                            W2AError(
                                path=e.get("path", "$"),
                                message=e.get("message", ""),
                                fix=e.get("fix"),
                            )
                            for e in data.get("errors", [])
                        ]
                        raise ManifestInvalid(origin, errors)
        except ManifestInvalid:
            raise
        except Exception:
            # Validation API unavailable — don't block discovery
            pass

    async def call(
        self,
        site: W2ASite,
        skill_id: str,
        headers: Optional[Dict[str, str]] = None,
        **params,
    ) -> Any:
        """
        Call a skill on a W2A-enabled site.

        Args:
            site: A W2ASite returned by discover().
            skill_id: The id of the skill to call.
            headers: Optional additional headers (e.g. auth tokens).
            **params: Keyword arguments matching the skill's input schema.

        Returns:
            Parsed JSON response from the skill endpoint.

        Raises:
            SkillNotFound: If skill_id doesn't exist on this site.
            SkillCallError: If the HTTP call fails.

        Example:
            result = await client.call(
                site, "search_products", q="running shoes", limit=10
            )
        """
        skill = site.get_skill(skill_id)
        if not skill:
            raise SkillNotFound(
                skill_id, [s.id for s in site.skills]
            )

        url = f"{site.origin}{skill.path}"
        session = await self._get_session()

        req_headers = {**(headers or {})}

        try:
            if skill.method in ("GET", "DELETE"):
                # Send params as query string
                async with session.request(
                    skill.method,
                    url,
                    params={k: v for k, v in params.items() if v is not None},
                    headers=req_headers,
                ) as resp:
                    if resp.status >= 400:
                        raise SkillCallError(skill_id, resp.status)
                    return await resp.json(content_type=None)
            else:
                # Send params as JSON body
                async with session.request(
                    skill.method,
                    url,
                    json={k: v for k, v in params.items() if v is not None},
                    headers=req_headers,
                ) as resp:
                    if resp.status >= 400:
                        raise SkillCallError(skill_id, resp.status)
                    return await resp.json(content_type=None)

        except SkillCallError:
            raise
        except Exception as e:
            raise SkillCallError(skill_id, 0, str(e)) from e


# ── Module-level convenience functions ──────────────────────────────────────

async def discover(
    url: str,
    timeout: int = 10,
    validate: bool = False,
) -> W2ASite:
    """
    Discover a W2A-enabled site.

    This is the main entry point for most use cases.

    Args:
        url: Site URL or domain. e.g. "stripe.com"
        timeout: Request timeout in seconds.
        validate: Validate manifest against the W2A spec.

    Returns:
        W2ASite object with skills and metadata.

    Raises:
        ManifestNotFound: Site has no agents.json.
        ManifestInvalid: Manifest exists but is invalid.

    Example:
        from w2a import discover

        site = await discover("w2a-protocol.org")
        print(site.skills)
    """
    client = W2AClient(timeout=timeout, validate=validate)
    try:
        return await client.discover(url)
    finally:
        await client.close()


def discover_sync(
    url: str,
    timeout: int = 10,
    validate: bool = False,
) -> W2ASite:
    """
    Synchronous version of discover() for non-async contexts.

    Uses asyncio.run() internally. Not suitable for use inside
    an existing event loop — use the async version there.

    Example:
        from w2a import discover_sync

        site = discover_sync("w2a-protocol.org")
        print(site.name)
    """
    return asyncio.run(discover(url, timeout=timeout, validate=validate))
