# Aelios → GPT Work MCP audit

Audit date: 2026-10-06 (Asia/Shanghai)

## Executive result

**Status: partial / blocked for an end-to-end GPT Work conclusion.** The requested local checkout was not present: the supplied workspace contained only `outputs/` and `work/`, with no `.git` directory and no source files. The private repository was nevertheless read through its Git remote at `main` commit `cfee873a1bc6420be2c3e128d3ef28bcb47cb9b6`; it contains only a one-line `README.md`. Therefore there is no private implementation to compare with Aelios and no evidence that the private project has an integration, deployment, permissions configuration, or import adapter.

The public upstream Aelios was read at `main` commit `2a9f636bc1879fe0bf1486cd9152adb282272388`. It implements a generic Streamable HTTP MCP endpoint with JSON-RPC memory tools. It does not, in the inspected tree, prove a GPT Work-specific app manifest, OAuth flow, account/project binding, approval policy, or live GPT Work registration. Aelios compatibility with a generic MCP-capable client is evidenced by code; GPT Work compatibility and real inference remain unverified.

## Evidence and scope

### Verified repository state

- Initial `git status --short`, branch, and remote checks in the requested workspace failed with `fatal: not a git repository`; listing showed only `outputs/` and `work/`.
- The private Git endpoint was readable with `git ls-remote`; `main` resolved to `cfee873a1bc6420be2c3e128d3ef28bcb47cb9b6`.
- A shallow, no-checkout read of that remote showed exactly one tracked path: `README.md`, blob `44627a2b71df6b935cb0ad77ec5247af845b5d47`. Its only line is `# siren-memory-lab`.
- The unauthenticated GitHub REST API returned `404 Not Found` for the private repository. This is recorded as an API-auth limitation, not evidence that the repository does not exist; Git smart transport access did succeed.
- No private real-chat, memory archive, OB data, or local import content was read.

Evidence URLs: [private repository](https://github.com/kirpearlzayneowo-afk/siren-memory-lab/tree/cfee873a1bc6420be2c3e128d3ef28bcb47cb9b6), [upstream audited commit](https://github.com/wusaki0723/Aelios/tree/2a9f636bc1879fe0bf1486cd9152adb282272388).

### Verified upstream implementation

- `src/index.ts:111-115,150-152` routes authenticated model traffic under `/<identity>/v1/...` and routes `/mcp` or `/memory-mcp` to `handleMcp`.
- `src/api/mcp.ts:925-967` exposes Streamable HTTP-style JSON-RPC over POST, supports `initialize`, `tools/list`, `tools/call`, ping, and batch requests. GET returns endpoint metadata and tool names without performing MCP authentication. POST authenticates first.
- `src/api/mcp.ts:61-69,943-944` accepts a `token` query parameter when no Authorization header is present, translating it into `Bearer`; bearer authentication and `x-api-key` are also accepted by `src/auth/apiKey.ts:15-20`.
- `src/auth/apiKey.ts:23-45` compares client-supplied credentials against Worker secrets including `CHATBOX_API_KEY` and `MEMORY_MCP_API_KEY`.
- `src/config/keyProfiles.ts:4-34` gives the MCP profile `memory:read`, `memory:write`, and `export:read`, fixed namespace `default`, and `chooseNamespace: false`. The Chatbox profile has broader gateway and memory scopes and can choose a namespace.
- `src/api/mcp.ts:670-693` confirms `memory_ingest` writes supplied raw messages to a D1-backed conversation. `:610-623` requires both read and export scopes for `memory_export`; the tool returns active memory content plus metadata.
- `src/api/mcp.ts:646-668,736-846` contains destructive or mutating MCP operations including delete, pin, glossary set, upsert, supersede, and archive, guarded by `memory:write` but not by a separate GPT Work approval layer.
- `src/gateway/record.ts:47-102` persists gateway exchanges and user/assistant message text to D1/FTS for non-auxiliary turns; it also invokes the remember-now path for human utterances. `:30-44` caps the captured user text at 8,000 characters and derives conversation/request IDs from request/session data.
- `README.md:9-12,90-94` describes the gateway as storing raw conversations first and consolidating them overnight. `wrangler.toml:10-27,65-82` enables persistent observability logs, a daily cron, seven-day message retention, and Cloudflare D1/Vectorize/AI bindings.
- `package.json:9-12,20` shows deployment runs `setup:cloudflare` before `wrangler deploy`; the repository also exposes `deploy:bare`, but the README says not to use bare deployment because resources are not created.

Upstream source links: [`src/api/mcp.ts`](https://github.com/wusaki0723/Aelios/blob/2a9f636bc1879fe0bf1486cd9152adb282272388/src/api/mcp.ts), [`src/auth/apiKey.ts`](https://github.com/wusaki0723/Aelios/blob/2a9f636bc1879fe0bf1486cd9152adb282272388/src/auth/apiKey.ts), [`src/config/keyProfiles.ts`](https://github.com/wusaki0723/Aelios/blob/2a9f636bc1879fe0bf1486cd9152adb282272388/src/config/keyProfiles.ts), [`src/gateway/record.ts`](https://github.com/wusaki0723/Aelios/blob/2a9f636bc1879fe0bf1486cd9152adb282272388/src/gateway/record.ts), [`wrangler.toml`](https://github.com/wusaki0723/Aelios/blob/2a9f636bc1879fe0bf1486cd9152adb282272388/wrangler.toml).

## GPT Work MCP boundary

### Verified

The upstream supplies a public HTTP endpoint shape and MCP JSON-RPC implementation. A generic MCP client could be configured with a URL such as `https://<worker>/mcp` and a credential, subject to the Worker being deployed and secrets/bindings being configured. The README calls out Claude Code and Codex and documents `https://<Worker address>/mcp?token=<CHATBOX_API_KEY>` (`README.md` around the “MCP memory” section).

### Unverified

- No GPT Work connector/app manifest, remote MCP registration, OAuth metadata, dynamic client registration, consent screen, tool approval policy, or GPT Work-specific header contract was found in the upstream tree or the private repository.
- No live Worker URL, Cloudflare account, secret values, D1 database, Vectorize index, queue, or GPT Work session was available to test.
- No real MCP handshake or tool call was made. Command success only established that source objects could be read.
- No deployment, service start, dependency install, typecheck, tests, or network inference was run, by design.

### Inference / boundary risk

The documented `token` query URL is convenient for clients but places a bearer-equivalent secret in a URL. URLs can enter browser history, proxy/access logs, screenshots, copied configuration, or referrer paths. Prefer a client-supported Authorization header or `x-api-key`; if GPT Work only supports a URL credential, treat the token as exposed and rotate it when configuration is shared. This is a security inference from the query-token implementation, not an observed leak.

The fixed MCP profile is intentionally narrow in model access (no `chat:proxy`) but still has full memory write and export capabilities. A GPT Work tool invocation could therefore import raw chats or mutate/export memories if the credential is granted and the client permits the call. There is no upstream evidence of a separate per-tool approval or read-only mode. Use a dedicated `MEMORY_MCP_API_KEY`, keep it in Cloudflare Secret storage, and do not give GPT Work the broader `CHATBOX_API_KEY` unless gateway access and cross-namespace behavior are explicitly intended.

Namespace isolation is a material integration question: the dedicated MCP profile is fixed to `default`, while the Chatbox profile can choose a namespace. A GPT Work connection using the dedicated key should be treated as operating only in `default`; a client using the shared Chatbox key may have a broader scope than the name “MCP memory” suggests.

## Real-chat import risks

The `memory_ingest` path is a write path, not a dry-run or review-only import. It stores accepted user-provided messages in the selected namespace; the upstream README says raw conversations are later processed by the overnight Dream pass. Risks include:

- accidental import of system prompts, tool results, secrets, personal data, or unrelated conversation turns;
- retention and secondary processing: D1/FTS storage, Vectorize/memory extraction, nightly judging/rollups, and configured observability all expand the data surface;
- namespace misbinding, especially if a client uses a shared key or sends a namespace field that the profile is not allowed to choose;
- duplicate or malformed transcript ordering, role/content normalization, and unsupported multimodal parts; these were not exercised against a real transcript;
- subsequent MCP tools can export active memories or mutate/delete them, so “import only” cannot be assumed from the endpoint alone.

No real chat content was read or imported during this audit. A safe future validation should use synthetic fixtures only, a dedicated namespace/key, explicit allowlisted roles and fields, redaction before transport, bounded batch sizes, and a reversible dry-run/report step outside the current upstream endpoint.

## Deployment and data-flow risks

1. **Unproven deployment state.** `npm run deploy` performs Cloudflare resource setup and deployment. This audit did not run it. A successful build or command would not prove the Worker, D1, Vectorize, Queue, secrets, or GPT Work registration are live.
2. **Secret handling.** `CHATBOX_API_KEY`, `MEMORY_MCP_API_KEY`, and upstream tokens are intended as Worker secrets. A leaked query token or historical secret requires rotation; do not put values in tracked `wrangler.toml` or GPT configuration shared with others.
3. **Persistent data.** Gateway requests and responses are persisted for memory behavior; message retention is configured as seven days, but extracted memories and other rollups have separate lifecycle behavior. “Seven-day retention” does not mean the conversation disappears from all derived stores after seven days.
4. **Operational logs.** Persistent observability is enabled in `wrangler.toml`. The code also logs operational identifiers and recall decisions. Review Cloudflare log access and retention before sending sensitive material.
5. **Authorization breadth.** MCP write/export/delete operations rely on bearer-style API keys and scopes. There is no evidence here of GPT Work user identity propagation, per-user tenancy, OAuth audience validation, or approval enforcement.
6. **License/dependency boundary.** The upstream declares AGPL-3.0-only and uses Cloudflare Workers/D1/Vectorize. A private deployment or modified network service needs a separate licensing and supply-chain review; no dependency installation or license compliance assessment was performed.

## Recommended next evidence, when authorized

- Provide or attach the intended private-repo checkout at a known Git root, or provide authenticated read access for its tree/history; do not send real chat archives.
- Identify the exact GPT Work MCP registration mechanism and required auth contract. Compare it with Aelios’ plain URL + bearer/query-token interface before enabling any write tool.
- Deploy only in a disposable Cloudflare account with synthetic data and a dedicated MCP key; verify `initialize`, `tools/list`, one read, and one explicitly approved write, then verify D1/Vectorize/Queue behavior and deletion/retention.
- Make the first integration read-only by policy and omit `memory_ingest`, export, delete, supersede, archive, pin, and upsert until user approval and data-flow controls are demonstrated.

## Audit limitations

This report is evidence-based against the private remote’s single `main` commit and upstream `main` commit listed above. It does not claim that the private repository has no unpushed/local files, that any Worker is deployed, that GPT Work can connect, or that real MCP inference succeeds. No OB data, private real-chat content, deployment, account operation, or source modification other than this report was performed.

## 2026-10-07 restricted implementation evidence

- The private repository was cloned into the current session checkout and a new branch `audit/aelios-current` was created from private `main` `cfee873a1bc6420be2c3e128d3ef28bcb47cb9b6`. The pre-existing report was copied unchanged before import and remains at this path.
- Aelios was fetched as remote `upstream/main` at `2a9f636bc1879fe0bf1486cd9152adb282272388`.
- Import used an `aelios/` tree prefix, so the private repository's root `README.md` and history remain intact while Aelios' original internal paths, including `aelios/LICENSE`, `aelios/src/`, `aelios/migrations/`, `aelios/tests/`, and `aelios/wrangler.toml`, are preserved. The import contains 185 upstream files.
- The import commit is `739e7e4c60dabe187b32216bf251eab1725a08de`, with parents `cfee873a1bc6420be2c3e128d3ef28bcb47cb9b6` and `2a9f636bc1879fe0bf1486cd9152adb282272388`. Both private and upstream commits are ancestors of the branch HEAD, preserving upstream history without merging into `main`.
- Non-deployment checks passed: branch name, clean status after commit, presence of `aelios/LICENSE`, `aelios/src/api/mcp.ts`, and this report, 185 imported Aelios paths, and ancestor checks for both parents. No dependencies were installed, no service was started, no Cloudflare operation was run, and no real chat or OB content was accessed.
- GPT Work MCP integration, live deployment, authentication behavior against a real endpoint, and real inference remain unverified exactly as stated above.

## 2026-10-07 read-only MCP implementation

On branch `work/read-only-mcp`, the MCP surface is restricted by an explicit allowlist. `tools/list` exposes only `memory_search`, `memory_list`, `memory_get`, `memory_boot`, `memory_recall`, and `diary_get`. `tools/call` rejects all other names, including `memory_ingest`, `memory_export`, `memory_delete`, `memory_upsert`, `memory_supersede`, `memory_archive`, `memory_pin`, `memory_create`, and `glossary_set`, before argument parsing or storage access. The change is in `aelios/src/api/mcp.ts`; coverage is in `aelios/tests/mcp-read-only.test.ts`.

The test is protocol-level and uses a synthetic request plus a stub environment; it does not read or write real D1 data. Dependencies were not installed, so execution of the TypeScript test remains an environment limitation until an existing dependency runtime is available. GPT Work registration, deployment, live MCP handshake, and real inference remain unverified.
