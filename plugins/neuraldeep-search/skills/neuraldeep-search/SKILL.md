---
name: neuraldeep-search
description: >
  Global search skill powered by NeuralDeep Search API (api.neuraldeep.ru/v1/search/*).
  Enables web search, Telegram channel search, site crawling, and quota checks.
  Automatically activates when user asks for search, research, fresh data, or current events.
metadata:
  version: 2.0.0
  neuraldeep:
    emoji: "🔍"
    base_url: "https://api.neuraldeep.ru/v1"
    endpoints:
      - /v1/search/web
      - /v1/search/tg
      - /v1/search/crawl
      - /v1/search/quota
---

> **Author:** these skills were authored by the **kimi2.6** and **qwen3.8 27b** models, and are published by **viktor-drobek**.

# NeuralDeep Search

Use this skill whenever the user needs:
- Web search or up-to-date information from the internet
- Research on topics not present in the local codebase or conversation
- Telegram channel search (Russian-language sources)
- Site crawling / fetching specific pages for RAG or fact-checking
- Checking remaining search quota

## Requirements

Python 3.10+ is sufficient; the helper uses only the standard library.
Run commands from this skill's directory. No `curl`, `jq`, or `httpx` is required.

The helper reads the key from `NEURALDEEP_SEARCH_API_KEY`, this skill's own variable, then
from the shared `NEURALDEEP_API_KEY`. Each is taken from the environment first,
then from `${CODDY_HOME:-~/.coddy}/.env`, the file Coddy loads at startup, so
a key added there works without a restart. A variable may hold several keys
separated by commas: before a billed request the helper uses the first key
whose free subscription and quota checks pass, and records its number (never
the key) in the state, so `resume` uses the same key. The Coddy provider file
is not read. The helper never prints a key. Without one it returns `blocked`,
naming the variable: ask the user to add it to `~/.coddy/.env` themselves,
for example `NEURALDEEP_SEARCH_API_KEY=sk-...`, never in the chat.

Read [Starter and Relay safety](STARTER_RELAY.md) before submitting work.
Every billed operation must pass the helper's live subscription, public-price,
and service-quota checks. A chat `decision.can_request=false` is not a service
quota decision. State files and artifacts are private runtime data, not repo files.

## Base URL

```
https://api.neuraldeep.ru/v1
```

---

## 1. Web Search

Search the open web for fresh data, articles, docs, and news.

### Guarded helper example
```bash
printf '%s\n' '{"query":"public API documentation","limit":3}' > request.json
python3 scripts/client.py run web --payload request.json --state web-state.json --output web-result.json
```

### Python example
```python
import json
from pathlib import Path
import subprocess
Path("request.json").write_text(json.dumps({"query": "public API documentation", "limit": 3}))
subprocess.run(["python3", "scripts/client.py", "run", "web", "--payload", "request.json",
                "--state", "python-web-state.json", "--output", "web-result.json"], check=True)
data = json.loads(Path("web-result.json").read_text())
for item in data["results"]:
    print(item.get("title"), item.get("url"))
```

### Parameters
- `query` (string, required) — search query
- `limit` (integer, optional) — max results, default 5
- `include_snippets` (boolean, optional) — include text snippets

### Response shape
```text
{
  "success": true,
  "results": [
    {"index": 1, "title": "...", "url": "...", "content": "...", "date": ""}
  ],
  "total": 3,
  "query": "...",
  "cost": 15,
  "quota": {"pool": "search", "mode": "tier", "day": {...}, "month": {...}}
}
```

---

## 2. Telegram Search

Search NeuralDeep's indexed Telegram channel database.

### Guarded helper example
```bash
printf '%s\n' '{"q":"public API documentation","limit":3}' > tg-request.json
python3 scripts/client.py run tg --payload tg-request.json --state tg-state.json --output tg-result.json
```

### Python example
```python
import subprocess
subprocess.run(["python3", "scripts/client.py", "run", "tg", "--payload", "tg-request.json",
                "--state", "python-tg-state.json", "--output", "tg-result.json"], check=True)
```

### Parameters (query string)
- `q` (string, required) — search query
- `limit` (integer, optional) — max results

### Illustrative response shape
Unlike web and crawl, the Telegram response has no `success` or `cost` field.
```text
{
  "results": [
    {"channel": "neuraldeep", "text": "...", "date": "...",
     "message_url": "...", "message_id": 123, "views_count": 100,
     "forwards_count": 0, "replies_count": 0, "reactions": {},
     "category": "...", "score": 0.9, "source": "...", "file_path": null}
  ],
  "total": 1,
  "query": "...",
  "search_type": "...",
  "sources": ["..."],
  "quota": {"pool": "search", "mode": "tier", "day": {...}, "month": {...}}
}
```

---

## 3. Site Crawl

Crawl a specific website to extract multiple pages.

### Guarded helper example
```bash
printf '%s\n' '{"url":"https://example.com","limit":3}' > crawl-request.json
python3 scripts/client.py run crawl --payload crawl-request.json --state crawl-state.json --output crawl-result.json
```

### Python example
```python
import subprocess
subprocess.run(["python3", "scripts/client.py", "run", "crawl", "--payload", "crawl-request.json",
                "--state", "python-crawl-state.json", "--output", "crawl-result.json"], check=True)
```

### Parameters
- `url` (string, required) — starting URL
- `limit` (integer, optional) — max pages to fetch
- `depth` (integer, optional) — crawl depth (default 1)

### Illustrative response shape
```text
{
  "success": true,
  "pages": [
    {"url": "...", "title": "...", "content": "...", "char_count": 1234}
  ],
  "total": 1,
  "cost": 15,
  "quota": {"pool": "crawl", "mode": "tier", "day": {...}, "month": {...}}
}
```

---

## 4. Quota Check

Check remaining search quota. Search and crawl have separate buckets.

### Guarded helper example
```bash
python3 scripts/client.py check web
python3 scripts/client.py check crawl
```

### Verified quota structure

`GET /v1/search/quota` returns top-level `tier`, with separate `search` and
`crawl` objects. Each has `mode: "tier"` and `day.remaining` / `month.remaining`.
The helper requires both windows to cover the operation. Read live values;
do not infer a budget from a pricing tier's advertised ceiling.

---

## Usage Workflow

1. **Resolve the API key** using the helper above.
2. **Check quota before every billed operation** (the helper always does):
   ```bash
   python3 scripts/client.py check web
   ```
3. **Execute the appropriate endpoint** based on user intent:
   - General web facts → `v1/search/web`
   - Russian Telegram sources → `v1/search/tg`
   - Deep dive into a specific site → `v1/search/crawl`
4. **Parse JSON** and present results concisely with source URLs.

## Paying from the wallet

A NeuralDeep key pays either from a subscription or from the rouble wallet, never
both (the mode is switched per key at <https://hub.neuraldeep.ru/app/keys>). In
wallet mode the subscription quota does not apply and every operation costs money
at the public price list. The helper therefore:

- prefers a subscription key: with several keys, a wallet key is considered only
  when no subscription key passes its quota check;
- never spends from the wallet on its own. `check` and `run` end with the status
  `wallet_approval_required`, the price, the estimated cost (the quota units times
  the price, rounded up to whole kopecks) and the wallet balance, for example:

  ```text
  Key 1 of NEURALDEEP_API_KEY pays from the wallet, not a subscription: about 2.00 RUB
  (1 x 2 RUB for search:web), wallet balance 370.05 RUB. Ask the user whether to pay;
  only after a clear yes, run again with --wallet-limit 2.00
  ```
- pays only with `--wallet-limit RUB`, the roubles the user approved for this run,
  and blocks before any request when the estimate exceeds that limit, the wallet
  balance, or the key's own spending cap.

**Show the warning to the user and wait for an explicit yes to that amount.**
Never pass `--wallet-limit` on your own, never raise an approved amount, and treat
a "no" or no answer as the end of the task. After a yes, run the same command as `run` with `--wallet-limit` set to the approved amount.
The estimate uses the public price list and the same units as the quota; the
provider may round or count differently, so it is an estimate, not an invoice.

```bash
python3 scripts/client.py check web
```

## Error handling

The helper explains an HTTP error with a fixed text for its status, never the
provider's response body, and adds `Retry-After` (whole seconds) and `X-Window`
(`session` or `week`) when the provider sends well-formed values, for example
`HTTP 429 (quota or rate limit reached); retry after 30 s; window week; no
automatic retry`. It never retries by itself. What a failure means depends on
when it happens:

- during the preflight GETs, before anything is billed: `blocked`;
- on the billed submission: `reconciliation_required`, since the work may have
  been charged; reconcile with the provider's records, never submit blindly again;
- while polling an existing job: `poll_error`; resume the same job later.

| Code | What the provider documents | What to do |
|---|---|---|
| `400` | Invalid request body, or a request longer than allowed | Fix the input; a billed submission is reconciled first |
| `401` | Key invalid or revoked, or not subscribed to the model | Ask the user to check the key in `NEURALDEEP_SEARCH_API_KEY` (or `NEURALDEEP_API_KEY`) in the environment or `~/.coddy/.env`; never read the file yourself |
| `408` | Upstream timeout after the provider's own retries | Reconcile a submission; resume a job |
| `422` | A parameter outside the allowed values | Fix the parameter |
| `429` | A quota or rate limit; `X-Window` names the session or week window and `Retry-After` the wait | Check the quota with `check`; wait, then decide explicitly |
| `500` | Internal error; the provider suggests repeating | Reconcile a submission before any new one; resume a job |
| `502` | Upstream unavailable; usually passes on its own | Reconcile or resume as above |
| `503` | Temporarily unavailable, with `Retry-After` | Wait; reconcile or resume as above |

Any other status is reported as `HTTP <code>` without a hint. A transport
failure or an unreadable answer is `Transport or response error`, with the same
outcomes.

- `400` usually means malformed parameters: verify the query encoding and the JSON payload.
- `check web` (or `tg`, `crawl`) reads `GET /v1/search/quota` to see the remaining search and crawl buckets.

## Cost & Limits

- Search API has its **own quota bucket**, separate from chat completions.
- Rate limits and daily quotas depend on the NeuralDeep Hub tariff (starter, pro, etc).
- Web and crawl responses include a `cost` field; Telegram responses do not. On a
  Starter subscription each request takes one unit from the day and month buckets
  in `quota`, whatever `cost` says.
- Consult `v1/search/quota` before heavy batch operations.

## Privacy & Security

- Do not log or expose the full API key.
- Do not send internal/private repository content to search endpoints as queries unless authorized.
- Search queries leave the local machine; treat query content as potentially external.
- SSRF guard blocks private networks and localhost; do not try to route to 10.x, 192.168.x, or 127.0.0.1.
