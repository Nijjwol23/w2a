# W2A SDK

Agent developer SDKs for the [Web2Agent Protocol](https://w2a-protocol.org).

One file at `/.well-known/agents.json` tells any AI agent what a website can do.
These SDKs are how your agent reads and uses that file.

---

## Packages

| Package | Runtime | Install |
|---------|---------|---------|
| `w2a` | Python 3.9+ | `pip install w2a` |
| `w2a-client` | Node.js / Browser / Edge | `npm install w2a-client` |
| `w2a-mcp` | MCP (Claude, Cursor, Cline) | `npm install -g w2a-mcp` |

---

## Python — 30 second start

```python
import asyncio
from w2a import discover

async def main():
    site = await discover("w2a-protocol.org")

    print(f"Connected to: {site.name}")
    print(f"Skills available: {len(site.skills)}\n")

    for skill in site.public_skills:
        print(f"  {skill.id}")
        print(f"  {skill.intent}")
        print(f"  {skill.action}\n")

asyncio.run(main())
```

---

## JavaScript / TypeScript

```typescript
import { discover } from 'w2a-client'

const site = await discover('w2a-protocol.org')

console.log(`${site.name} — ${site.skills.length} skills`)

// Find a skill by natural language
const validator = site.findSkill('validate')
console.log(validator?.action) // POST /api/validate

// Call a skill directly
const client = new W2AClient()
const result = await client.call(site, 'check_site', { url: 'stripe.com' })
```

---

## MCP — Claude Desktop / Cursor

Add to your `~/.claude/claude_desktop_config.json`:

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

Every skill in the site's `agents.json` becomes a tool Claude can call.

---

## LangChain

```python
from w2a.integrations.langchain import W2ATool
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI

# Each W2A skill becomes a LangChain tool
tools = await W2ATool.from_url("w2a-protocol.org")

llm = ChatOpenAI(model="gpt-4")
agent = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS)
result = agent.run("Check if stripe.com is W2A enabled")
```

---

## Handling sites without W2A

Not every site has adopted W2A yet. Handle it gracefully:

```python
from w2a import discover
from w2a.exceptions import ManifestNotFound

try:
    site = await discover("stripe.com")
    # Use W2A skills
except ManifestNotFound:
    # Fall back to your own approach
    print("Site not W2A-enabled yet")
```

```typescript
import { discover, ManifestNotFoundError } from 'w2a-client'

try {
  const site = await discover('stripe.com')
} catch (err) {
  if (err instanceof ManifestNotFoundError) {
    // Site hasn't adopted W2A yet
  }
}
```

---

## Repository structure

```
sdk/
├── python/          pip install w2a
│   ├── w2a/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── models.py
│   │   └── exceptions.py
│   ├── pyproject.toml
│   └── README.md
├── javascript/      npm install w2a-client
│   ├── src/
│   │   └── index.ts
│   └── package.json
└── mcp/             npm install -g w2a-mcp
    ├── src/
    │   └── index.js
    └── package.json

integrations/
└── langchain/       from w2a.integrations.langchain import W2ATool
    └── tool.py
```

---

## The protocol

`agents.json` format, spec, and validator: [github.com/Nijjwol23/w2a](https://github.com/Nijjwol23/w2a)

Generate a manifest for your site: [w2a-protocol.org/tools](https://w2a-protocol.org/tools)

---

Apache 2.0 · [w2a-protocol.org](https://w2a-protocol.org)
