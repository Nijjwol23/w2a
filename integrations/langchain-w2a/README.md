# langchain-w2a

[![PyPI version](https://img.shields.io/pypi/v/langchain-w2a)](https://pypi.org/project/langchain-w2a)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Tests](https://img.shields.io/badge/standard%20tests-langchain-blue)](https://docs.langchain.com/oss/python/contributing/standard-tests-langchain)

LangChain integration for the [Web2Agent Protocol](https://w2a-protocol.org).

Turns any W2A-enabled website's declared skills into typed LangChain tools — one tool per skill, with Pydantic input schemas built from the site's `agents.json`.

```bash
pip install langchain-w2a
```

---

## What is W2A?

W2A is an open standard where websites declare their capabilities at `/.well-known/agents.json`. Instead of crawling 40–50 pages to understand what a site does, your agent reads one file.

```
robots.txt  →  what not to crawl  (1994)
sitemap.xml →  where pages are    (2005)
agents.json →  what a site can do (2026)
```

---

## Three ways to use it

### 1. Toolkit — typed tools from a known site

```python
from langchain_w2a import W2AToolkit
from langchain.agents import create_agent

# Each W2A skill becomes a typed LangChain tool
toolkit = await W2AToolkit.from_url("w2a-protocol.org")
tools = toolkit.get_tools()

agent = create_agent(model="claude-sonnet-4-5-20250929", tools=tools)
agent.invoke({"messages": [("user", "Check if stripe.com is W2A enabled")]})
```

### 2. Generic discover + call tools

```python
from langchain_w2a import W2ADiscoverTool, W2ASkillTool

tools = [W2ADiscoverTool(), W2ASkillTool()]
# Agent can now discover and call any W2A-enabled site at runtime
```

### 3. Direct invocation

```python
from langchain_w2a import W2ADiscoverTool

discover = W2ADiscoverTool()
result = discover.invoke({"url": "w2a-protocol.org"})
print(result)  # JSON summary of site's declared skills
```

---

## Standard tests

This package implements LangChain's [standard test suite](https://docs.langchain.com/oss/python/contributing/standard-tests-langchain) for tool integrations.

```bash
# Install test dependencies
pip install "langchain-w2a[test]"

# Run unit tests
pytest tests/unit_tests/

# Run integration tests (requires internet)
pytest tests/integration_tests/
```

---

## Handling sites that haven't adopted W2A yet

```python
result = discover.invoke({"url": "stripe.com"})
# "stripe.com has not adopted the W2A protocol yet —
#  no /.well-known/agents.json found.
#  Generate one at https://w2a-protocol.org/tools"
```

Tools fail gracefully on non-W2A sites so your agent can fall back to other strategies.

---

## Requirements

- Python 3.9+
- `langchain-core >= 0.2`
- `w2a >= 0.1.0` (the W2A Python SDK)
- `pydantic >= 2.0`

---

## Documentation

- **LangChain docs:** [docs.langchain.com/oss/python/integrations/tools/w2a](https://docs.langchain.com/oss/python/integrations/tools/w2a) (pending)
- **W2A protocol:** [w2a-protocol.org](https://w2a-protocol.org)
- **Spec:** [github.com/Nijjwol23/w2a](https://github.com/Nijjwol23/w2a)

---

## License

Apache 2.0 — same as LangChain.
