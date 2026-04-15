"""
W2A exceptions — clean error hierarchy for agent developers.
"""


class W2AException(Exception):
    """Base exception for all W2A errors."""
    pass


class ManifestNotFound(W2AException):
    """
    Raised when a site does not serve /.well-known/agents.json.

    This is not necessarily an error — the site may simply not have
    adopted W2A yet. Handle gracefully and fall back to crawling.

    Example:
        try:
            site = await discover("example.com")
        except ManifestNotFound:
            # site not W2A-enabled, fall back to your own discovery
            pass
    """

    def __init__(self, url: str):
        self.url = url
        super().__init__(
            f"No W2A manifest found at {url}/.well-known/agents.json — "
            f"this site has not adopted the W2A protocol yet."
        )


class ManifestInvalid(W2AException):
    """
    Raised when a manifest exists but fails validation.

    Includes the list of validation errors for debugging.
    """

    def __init__(self, url: str, errors: list):
        self.url = url
        self.errors = errors
        error_summary = "; ".join(str(e) for e in errors[:3])
        super().__init__(
            f"W2A manifest at {url} is invalid: {error_summary}"
        )


class SkillNotFound(W2AException):
    """
    Raised when a requested skill id does not exist in the manifest.
    """

    def __init__(self, skill_id: str, available: list):
        self.skill_id = skill_id
        self.available = available
        super().__init__(
            f"Skill '{skill_id}' not found. "
            f"Available: {', '.join(available)}"
        )


class SkillCallError(W2AException):
    """
    Raised when a skill HTTP call fails.
    """

    def __init__(self, skill_id: str, status_code: int, message: str = ""):
        self.skill_id = skill_id
        self.status_code = status_code
        super().__init__(
            f"Skill '{skill_id}' call failed with HTTP {status_code}"
            + (f": {message}" if message else "")
        )
