# Novel design documentation

This directory is the canonical English documentation for the public
`noory-code/novel-ai` plugin stack. Public plugin behavior is governed by these
documents, package-level implementation documents, code, and executable tests.
Private product documents may add commercial-app context, but they do not
override the public plugin contracts defined here.

## Reading order

| Order | Document | Purpose |
|---|---|---|
| 1 | [VISION.md](./VISION.md) | Novel's essence, identity, and three-phase workflow |
| 2 | [PHILOSOPHY.md](./PHILOSOPHY.md) | Product and service-design principles |
| 3 | [ARCHITECTURE.md](./ARCHITECTURE.md) | Open-core boundary and dependency direction |
| 4 | [concepts/](./concepts/) | Canvas, kind, and AI-collaboration meanings |
| 5 | [specs/](./specs/) | Behavior, schema, storage, domain, and format F contracts |
| 6 | [plans/](./plans/) | Design history and unresolved artifact-flow proposals |

## Canonical homes

| Concern | Canonical location |
|---|---|
| Essence and identity | [VISION.md](./VISION.md) |
| Value theory | [PHILOSOPHY.md](./PHILOSOPHY.md) |
| Open-core system boundary | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| Canvas and kind meaning | [concepts/](./concepts/) |
| Canvas behavior and wire fields | [specs/](./specs/) |
| Mashbill implementation details | [`mashbill/docs/`](../mashbill/docs/) |
| Publish contract between Mashbill and Solera | [specs/format-f.md](./specs/format-f.md) |
| Decision history | [`mashbill/docs/DECISIONS.md`](../mashbill/docs/DECISIONS.md) |

## Repository boundary

- Mashbill, Solera, Proof, and Distill are public MIT plugins in this repository.
- The commercial Novel application is a separate private product that may host
  these engines through their public MCP, HTTP, file-format, and format F
  contracts.
- Public plugins must not import or path-reference private application code.
- Cross-plugin integration uses files and stable identifiers, never sibling
  Python imports.

Historical decisions may mention the former `noory-ai/<package>` locations.
Those references describe where a change happened at the time; all current
source, installation, and contribution paths use `noory-code/novel-ai`.
