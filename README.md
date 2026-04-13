# W2A — Web2Agent Protocol

> The missing layer of the agentic web stack.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Spec](https://img.shields.io/badge/spec-v0.1_draft-purple)](spec/v0.1.md)
[![A2A Compatible](https://img.shields.io/badge/A2A-compatible-green)](https://a2a-protocol.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Website](https://img.shields.io/badge/website-w2a--protocol.org-blue)](https://w2a-protocol.org)

```
MCP   Agent ↔ Tools     modelcontextprotocol.io
A2A   Agent ↔ Agent     a2a-protocol.org
W2A   Agent ↔ Web       w2a-protocol.org        ← you are here
```

---

## The problem

Every AI agent that visits a website today operates blind.

It crawls page after page — sometimes 40 to 50 requests — just to
understand what a site does, what actions it supports, and how to
interact with it. There is no standard for a website to declare
itself to an AI agent. No handshake. No map. Just brute-force
discovery.

A2A defines how agents talk to agents. MCP defines how agents talk
to tools. Nobody has defined how agents talk to the open web.

W2A defines it.

---

## The solution

A single file — `agents.json` — served at `/.well-known/agents.json`.

```json
{
  "w2a": "1.0",
  "site": {
    "name": "Acme Store",
    "type": "ecommerce"
  },
  "capabilities": [
    {
      "id": "search_products",
      "intent": "find products by query or category",
      "action": "GET /api/search",
      "input": { "q": "string", "category": "string?" },
      "output": { "items": "Product[]", "total": "int" },
      "auth": "none"
    },
    {
      "id": "add_to_cart",
      "intent": "add a product to the shopping cart",
      "action": "POST /api/cart/items",
      "input": { "sku": "string", "qty": "int" },
      "output": { "cart_id": "string", "subtotal": "float" },
      "auth": "session"
    },
    {
      "id": "checkout",
      "intent": "complete a purchase",
      "action": "POST /api/orders",
      "input": { "cart_id": "string", "payment_token": "string" },
      "output": { "order_id": "string", "status": "string" },
      "auth": "session"
    }
  ],
  "policies": {
    "rate_limit": "60/min",
    "allowed_agents": ["*"]
  }
}
```

An agent reads this once. It knows exactly what the site can do,
what to call, and how to call it — without loading a single page.

---

## Install

### Option 1 — CLI (recommended)

```bash
npx w2a@latest init
```

Auto-detects your framework. Registers `/.well-known/agents.json`.
Generates a draft manifest from your existing routes and schemas.
You review, approve, deploy.

| Framework | Adapter |
|-----------|---------|
| Next.js / Vercel | `@w2a/nextjs` |
| Express / Fastify | `@w2a/node` |
| WordPress | W2A Plugin |
| Shopify | W2A App |
| Ruby on Rails | `w2a-rails` |
| Django | `w2a-django` |

### Option 2 — Script tag

```html
<script
  src="https://cdn.w2a-protocol.org/v1.js"
  data-site="yoursite.com">
</script>
```

Reads your existing Schema.org JSON-LD, Open Graph tags, sitemap,
and HTML forms. Builds and serves the manifest via service worker.
Works on Squarespace, Wix, Webflow — any locked platform.

### Option 3 — DNS record

```
_w2a.yoursite.com  CNAME  edge.w2a-protocol.org
```

W2A's edge network intercepts agent requests, crawls your site
once, generates and caches the manifest. Auto-updates on a
schedule. Your origin server never sees agent traffic.

---

## How it works with A2A

Google's A2A protocol defines an **AgentCard** — a JSON file where
enterprise agents advertise capabilities to other agents. A2A is
built for Salesforce, SAP, Workday, ServiceNow. It has no
mechanism for the 200 million public websites that are not
enterprise software companies.

W2A fills this gap. An `agents.json` file is a valid A2A AgentCard
profile. Any A2A client reads it without modification. Every site
that adopts W2A becomes a discoverable node in the A2A ecosystem
automatically.

```json
{
  "w2a": "1.0",
  "a2a_profile": {
    "name": "Acme Store Agent",
    "url": "https://acme.com/.well-known/agents.json",
    "version": "1.0"
  }
}
```

---

## The lineage

```
1994  robots.txt     told crawlers what NOT to index
2005  sitemap.xml    told crawlers WHERE pages are
2025  agents.json    tells agents what a site can DO
```

---

## Spec v0.1

Full specification → [`spec/v0.1.md`](spec/v0.1.md)

### Top-level fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `w2a` | string | yes | Spec version. Always `"1.0"` |
| `site.name` | string | yes | Human-readable site name |
| `site.type` | string | yes | `ecommerce` `blog` `saas` `marketplace` `media` `other` |
| `site.language` | string | no | BCP 47 tag e.g. `"en"` |
| `capabilities` | array | yes | Declared capabilities. Minimum 1. |
| `policies` | object | no | Access control and rate limiting |
| `federation` | array | no | Links to external `agents.json` files |
| `a2a_profile` | object | no | A2A AgentCard compatibility block |

### Capability fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique slug e.g. `"search_products"` |
| `intent` | string | yes | Plain-English description the agent reads |
| `action` | string | yes | `METHOD /path` e.g. `"GET /api/search"` |
| `input` | object | no | Named input parameters with types |
| `output` | object | no | Named output fields with types |
| `auth` | string | yes | `none` `session` `bearer` `apikey` |

### Types

`string` `string?` `int` `float` `bool` `object` `string[]` `object[]`

---

## Examples

Full examples in [`/examples`](examples/).

- [`ecommerce.json`](examples/ecommerce.json)
- [`saas.json`](examples/saas.json)
- [`blog.json`](examples/blog.json)

---

## Roadmap

- [x] Spec v0.1 draft
- [ ] JSON Schema validator — `w2a validate`
- [ ] CLI generator — `npx w2a init`
- [ ] Next.js middleware — `@w2a/nextjs`
- [ ] Express / Fastify middleware — `@w2a/node`
- [ ] WordPress plugin
- [ ] Shopify app
- [ ] Edge network — Tier 0 DNS install
- [ ] W3C Community Group proposal
- [ ] IETF RFC draft — `/.well-known/` registration

---

## Repository structure

```
w2a/
├── spec/
│   └── v0.1.md
├── packages/
│   ├── core/
│   ├── generator/
│   └── cli/
├── adapters/
│   ├── nextjs/
│   ├── node/
│   ├── wordpress/
│   ├── shopify/
│   ├── rails/
│   └── django/
├── examples/
│   ├── ecommerce.json
│   ├── saas.json
│   └── blog.json
└── README.md
```

---

## Contributing

W2A is an open standard, not a product. No single company controls
it — the same model as A2A under the Linux Foundation.

- Review [`spec/v0.1.md`](spec/v0.1.md) and open issues
- Propose new capability types or policy fields
- Build an adapter for your framework
- Share feedback in [GitHub Discussions](../../discussions)

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR.

---

## Related standards

| Standard | What it does |
|----------|-------------|
| [A2A](https://a2a-protocol.org) | Agent↔Agent — Google / Linux Foundation |
| [MCP](https://modelcontextprotocol.io) | Agent↔Tools — Anthropic |
| [Schema.org](https://schema.org) | Structured data W2A reads as input |
| [RFC 8615](https://www.rfc-editor.org/rfc/rfc8615) | The `.well-known/` URI standard |

---

## License

Apache 2.0 — the same license as A2A. Intentionally.

This is an open standard and will remain one.

---

*Built by [@Nijjwol23](https://github.com/Nijjwol23) · open to the community*
