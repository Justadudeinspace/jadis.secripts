# AI advice and privacy

AI can help explain structured JS evidence, conflicts, build blockers and next
evidence needs. It cannot execute commands, grant permissions, mutate models, or
upgrade an evidence state. Model recommendations remain untrusted advice.

## Configure BYOK

OpenAI, Anthropic/Claude and DeepSeek use separate environment references:
OPENAI_API_KEY, ANTHROPIC_API_KEY and DEEPSEEK_API_KEY. Configure these privately
in your environment; never put a key in a command operand, receipt, Git file or report.
Claude keys that require a workspace can use ANTHROPIC_WORKSPACE_ID.

```sh
js ai setup
js ai prov --json
js ai models --provider openai
js ai models --provider openai --network
```

The catalog request is explicit, authenticated network access; no inference occurs.
Select an actual account model ID rather than relying on an old hardcoded default.
Requests use fixed official HTTPS origins, refuse redirects, ignore proxy environment
routing, have time/output limits and do not retry automatically. Offline/missing-key
errors remain clear; normal CI uses mocks, never paid calls.

## Inspect and approve context

Save only a report you intend to share using normal shell redirection. Then:

```sh
js ai context --context REPORT.json --json
js ai ask 'Why is this build blocked?' --provider openai --model MODEL --context REPORT.json --json
js ai ask 'Why is this build blocked?' --provider openai --model MODEL --context REPORT.json --send --approve SHA256 --json
```

The second command previews the exact question plus redacted context and its hash.
The third must use that hash. Changed files/questions require a fresh preview.
No implicit host scan, receipt upload, firmware blob or full log is sent. Input JSON
is capped at 256 KiB and outbound evidence at 12 KiB; truncation is explicit. Keys,
known identifiers and local paths are masked, but redaction cannot guarantee privacy.
Review every visible field. Provider-side retention policies still apply; OpenAI
Responses requests set store=false.

Receipts retain provider/context hash/result, not prompt/response bodies. The local
context-preview operation deliberately creates no body-retaining receipt. Advice
output is sanitized and labeled AI_ADVICE_NOT_EVIDENCE. Incomplete responses, tool
requests and malformed data fail rather than claiming successful advice.

## Tool contract

```sh
js ai tools registry.search recovery --json
js ai tools registry.show image.roundtrip --json
```

Local typed context tools expose registry metadata or an explicitly selected receipt
summary. These are human-invoked context previews, not autonomous model calls. The model
receives no function-execution contract and cannot route a shell or mutating operation.
Use ordinary JS operations yourself after reviewing any suggestion.

## Subscription authentication

Current official Sign in with ChatGPT supports eligible open-source/personal and selected
private clients; a valid implementation requires PKCE, state/nonce, JWKS identity checks,
account-bound credential refresh and streamed terminal-event handling. This private
client's eligibility and full credential lifecycle are unqualified: subscription login
is BLOCKED, not implemented via another client's tokens.

Anthropic documents API credits for eligible subscribers; claiming those credits in
the provider Console is distinct from reusing Claude Code session credentials. DeepSeek
uses its documented API authentication. No general third-party subscription authorization
was established for these adapters. API keys, API credits, API billing and subscription
access are different concepts. Consult current provider terms/account eligibility.

Official source relationships are recorded in the [research ledger](research/phase5-sources.json)
and [credits](../CREDITS.md). Live provider inference remains UNTESTED unless explicitly
qualified outside normal CI.
