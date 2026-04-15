"""
W2A Python SDK
The Web2Agent Protocol client for Python.

pip install w2a

Quick start:
    from w2a import discover
    site = await discover("stripe.com")
    for skill in site.skills:
        print(skill.id, "—", skill.intent)
"""

from .client import W2AClient, discover, discover_sync
from .models import W2ASite, W2ASkill, W2APolicy, W2AError
from .exceptions import (
    W2AException,
    ManifestNotFound,
    ManifestInvalid,
    SkillNotFound,
    SkillCallError,
)

__version__ = "0.1.0"
__all__ = [
    "W2AClient",
    "discover",
    "discover_sync",
    "W2ASite",
    "W2ASkill",
    "W2APolicy",
    "W2AError",
    "W2AException",
    "ManifestNotFound",
    "ManifestInvalid",
    "SkillNotFound",
    "SkillCallError",
]
