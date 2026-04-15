# W2A Governance

W2A is maintained by [The Order AI](https://theorder.ai) and open to
contributions from the community. The goal is a protocol no single
company controls — the same model as A2A under the Linux Foundation.

---

## Principles

- **Open standard.** No single company owns W2A. Apache 2.0.
- **Backwards compatible.** Existing manifests always remain valid.
- **Minimal by default.** The spec adds fields only when adoption
  demonstrates clear need.
- **A2A aligned.** Changes that affect A2A compatibility require
  explicit review against the A2A spec.

---

## How the spec evolves

### Minor changes (typos, clarifications, examples)
- Open a PR directly
- One reviewer approval required
- Merged without discussion period

### New optional fields
- Open a GitHub issue describing the use case
- 7-day public comment period
- Two independent reviewer approvals required
- Merged after comment period closes

### Breaking changes
- Must be proposed as a new major version (v2.0)
- 30-day public discussion period
- Requires sign-off from at least 3 independent adopters
- Old version remains supported for 12 months minimum

---

## Roles

**Maintainers** — merge PRs, manage releases, represent W2A in
external discussions. Current maintainers: [@Nijjwol23](https://github.com/Nijjwol23)

**Contributors** — anyone who opens a PR or issue.

**Adopters** — sites running W2A in production. Listed in
[ADOPTERS.md](ADOPTERS.md). Adopters have a voice in breaking change
decisions.

---

## IP Policy

All contributions are made under Apache 2.0. By submitting a PR
you confirm you have the right to license the contribution under
Apache 2.0 and agree to do so.

No CLA required. Developer Certificate of Origin (DCO) applies —
sign your commits with `git commit -s`.

---

## Roadmap toward foundation governance

1. ✓ Open spec published (Apache 2.0)
2. ✓ SDK published (Python, JS, MCP)
3. → IETF /.well-known/agents.json registration
4. → 10+ independent adopters
5. → W3C Community Group proposal
6. → Linux Foundation project proposal

W2A follows adoption, not the other way around.
Standards bodies ratify what the community has already decided works.

---

Questions? Open an issue or join the
[A2A discussions](https://github.com/a2aproject/A2A/discussions).
