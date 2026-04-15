"""
W2A data models — typed representations of the agents.json manifest.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class W2ASkill:
    """A single declared skill from an agents.json manifest."""

    id: str
    intent: str
    action: str
    auth: str
    input: Dict[str, str] = field(default_factory=dict)
    output: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None

    @property
    def method(self) -> str:
        """HTTP method extracted from action field. e.g. 'GET'"""
        return self.action.split(" ")[0].upper()

    @property
    def path(self) -> str:
        """URL path extracted from action field. e.g. '/api/search'"""
        parts = self.action.split(" ")
        return parts[1] if len(parts) > 1 else "/"

    @property
    def requires_auth(self) -> bool:
        """True if this skill requires any form of authentication."""
        return self.auth != "none"

    def __repr__(self) -> str:
        return f"W2ASkill(id={self.id!r}, intent={self.intent!r}, action={self.action!r})"


@dataclass
class W2APolicy:
    """Access and rate limit policies declared in agents.json."""

    rate_limit: Optional[str] = None
    allowed_agents: List[str] = field(default_factory=lambda: ["*"])
    blocked_agents: List[str] = field(default_factory=list)
    require_identity: bool = False

    @property
    def is_open(self) -> bool:
        """True if all agents are allowed."""
        return "*" in self.allowed_agents

    @property
    def requests_per_minute(self) -> Optional[int]:
        """Parse rate limit string to requests per minute."""
        if not self.rate_limit:
            return None
        try:
            amount, unit = self.rate_limit.split("/")
            amount = int(amount)
            if unit == "sec":
                return amount * 60
            elif unit == "min":
                return amount
            elif unit == "hour":
                return amount // 60
        except (ValueError, AttributeError):
            pass
        return None


@dataclass
class W2ASite:
    """
    A discovered W2A-enabled site.

    Returned by discover() and W2AClient.discover().
    Provides access to skills and the ability to call them.
    """

    name: str
    type: str
    origin: str
    manifest_url: str
    language: str = "en"
    description: Optional[str] = None
    skills: List[W2ASkill] = field(default_factory=list)
    policy: Optional[W2APolicy] = None
    a2a_compatible: bool = False
    w2a_version: str = "1.0"
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    def get_skill(self, skill_id: str) -> Optional[W2ASkill]:
        """Look up a skill by its id. Returns None if not found."""
        return next((s for s in self.skills if s.id == skill_id), None)

    def find_skill(self, intent_fragment: str) -> Optional[W2ASkill]:
        """
        Find a skill by searching intent strings.
        Useful for natural language skill selection.

        Example:
            skill = site.find_skill("search")
        """
        fragment = intent_fragment.lower()
        for skill in self.skills:
            if fragment in skill.intent.lower() or fragment in skill.id.lower():
                return skill
        return None

    def skills_by_auth(self, auth_type: str) -> List[W2ASkill]:
        """Return all skills with a specific auth type."""
        return [s for s in self.skills if s.auth == auth_type]

    @property
    def public_skills(self) -> List[W2ASkill]:
        """Skills that require no authentication."""
        return [s for s in self.skills if s.auth == "none"]

    def __repr__(self) -> str:
        return (
            f"W2ASite(name={self.name!r}, type={self.type!r}, "
            f"origin={self.origin!r}, skills={len(self.skills)})"
        )


@dataclass
class W2AError:
    """A validation error returned from the W2A validator."""

    path: str
    message: str
    fix: Optional[str] = None

    def __str__(self) -> str:
        base = f"{self.path}: {self.message}"
        if self.fix:
            base += f" → {self.fix}"
        return base
