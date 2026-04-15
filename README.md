# W2A — Web2Agent Protocol

> The open standard that makes any website agent-readable.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Spec](https://img.shields.io/badge/spec-v0.1_draft-purple)](spec/v0.1.md)
[![A2A Compatible](https://img.shields.io/badge/A2A-compatible-green)](https://a2a-protocol.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Website](https://img.shields.io/badge/website-w2a--protocol.org-blue)](https://w2a-protocol.org)

```
MCP   Agent ↔ Tools     modelcontextprotocol.io
A2A   Agent ↔ Agent     a2a-protocol.org
W2A   Agent ↔ Web       w2a-protocol.org        ← this repo
```

---

## For agent developers — use the SDK

### Python
```bash
pip install w2a
```
```python
from w2a import discover

site = await discover("stripe.com")
for skill in site.public_skills:
    print(skill.id, "—", skill.intent)
```

### JavaScript / TypeScript
```bash
npm install w2a-client
```
```typescript
import { discover } from 'w2a-client'

const site = await discover('stripe.com')
console.log(site.skills.map(s => s.intent))
```

### MCP — Claude Desktop / Cursor / Cline
```json
{
  "mcpServers": {
    "w2a": {
      "command": "npx",
      "args": ["w2a-mcp", "--url", "https://yoursite.com"]
    }
  }
}
```

### LangChain
```python
from w2a.integrations.langchain import W2ATool

tools = await W2ATool.from_url("w2a-protocol.org")
agent.add_tools(tools)
```

---

## For website owners — add agents.json

**Generate your manifest in 30 seconds:** [w2a-protocol.org/tools](https://w2a-protocol.org/tools)

Or create `/.well-known/agents.json` manually:

```json
{
  "w2a": "1.0",
  "site": {
    "name": "Acme Store",
    "type": "ecommerce"
  },
  "skills": [
    {
      "id": "search_products",
      "intent": "Find products by keyword or category",
      "action": "GET /api/search",
      "input": { "q": "string", "category": "string?" },
      "output": { "items": "Product[]", "total": "int" },
      "auth": "none"
    }
  ],
  "policies": {
    "rate_limit": "60/min",
    "allowed_agents": ["*"]
  }
}
```

**Validate it:**
```bash
curl -X POST https://w2a-protocol.org/api/validate \
  -H "Content-Type: application/json" \
  -d @.well-known/agents.json
```

**Check any site:**
```bash
curl "https://w2a-protocol.org/api/check?url=yoursite.com"
```

---

## The problem

Every AI agent visiting a website today crawls it blind — 40–50 HTTP
requests just to understand what a site does. No standard. No map.
Pure waste, multiplied by thousands of agents hitting every site daily.

```
robots.txt   →  what not to crawl    (1994)
sitemap.xml  →  where pages are      (2005)
agents.json  →  what a site can do   (2026)
```

---

## Repository structure

```
spec/
└── v0.1.md                    The W2A protocol specification

sdk/
├── python/                    pip install w2a
├── javascript/                npm install w2a-client
└── mcp/                       npx w2a-mcp

integrations/
└── langchain/                 LangChain W2ATool

ADOPTERS.md                    Sites running W2A
GOVERNANCE.md                  How the spec evolves
```

---

## Current adoption

| Site | Status |
|------|--------|
| w2a-protocol.org | ✓ enabled · 6 skills · A2A compatible |
| _your site here_ | [Add yours →](https://w2a-protocol.org/tools) |

---

## Governance

W2A is maintained by [The Order AI](https://theorder.ai) and open to
contributions. The goal is a protocol no single company controls —
the same model as A2A under the Linux Foundation.

Spec changes require two independent reviewers. Major changes go
through a public discussion period. See [GOVERNANCE.md](GOVERNANCE.md).

---

## Links

- **Live tools:** [w2a-protocol.org/tools](https://w2a-protocol.org/tools)
- **Research paper:** [The Agent Discovery Problem](https://w2a-protocol.org/blog/agent-discovery-problem)
- **A2A discussion:** [github.com/a2aproject/A2A/discussions](https://github.com/a2aproject/A2A/discussions)
- **Spec v0.1:** [spec/v0.1.md](spec/v0.1.md)

Apache 2.0 — same license as A2A. Intentionally.
