---
name: neuraldeep-images
description: >
  Image generation and processing skill powered by NeuralDeep Image API.
  Supports FLUX image generation, 4× upscale, background removal, enhancement,
  and avatar creation. Work asynchronously: submit → poll → download.
  Automatically activates when user asks for image generation, AI art,
  photo processing, or visual asset creation.
metadata:
  version: 2.0.0
  neuraldeep:
    emoji: "🖼️"
    base_url: "https://api.neuraldeep.ru/v1/images"
    endpoints:
      - /v1/images/generate
      - /v1/images/tasks/{uid}
      - /v1/images/tasks/{uid}/result
      - /v1/images/upscale
      - /v1/images/background/remove
      - /v1/images/enhance
      - /v1/images/avatar
---

> **Author:** these skills were authored by the **kimi2.6** and **qwen3.8 27b** models, and are published by **viktor-drobek**.

# NeuralDeep Image API

Use this skill whenever the user needs:
- Generating images from text prompts (FLUX)
- Upscaling existing images 4×
- Removing backgrounds
- Enhancing photos
- Creating avatars from portraits

## Requirements

Python 3.10+ is sufficient; the helper uses only the standard library.
Run commands from this skill's directory. No `curl`, `jq`, or `httpx` is required.

The helper reads the key from `NEURALDEEP_IMAGES_API_KEY`, this skill's own variable, then
from the shared `NEURALDEEP_API_KEY`. Each is taken from the environment first,
then from `${CODDY_HOME:-~/.coddy}/.env`, the file Coddy loads at startup, so
a key added there works without a restart. A variable may hold several keys
separated by commas: before a billed request the helper uses the first key
whose free subscription and quota checks pass, and records its number (never
the key) in the state, so `resume` uses the same key. The Coddy provider file
is not read. The helper never prints a key. Without one it returns `blocked`,
naming the variable: ask the user to add it to `~/.coddy/.env` themselves,
for example `NEURALDEEP_IMAGES_API_KEY=sk-...`, never in the chat.

Read [Starter and Relay safety](STARTER_RELAY.md) before submitting work.
Every billed operation must pass the helper's live subscription, public-price,
and service-quota checks. A chat `decision.can_request=false` is not a service
quota decision. State files and artifacts are private runtime data, not repo files.

## Base URL

```
https://api.neuraldeep.ru/v1/images
```

---

## 1. Image Generation (FLUX)

### Submit, poll, and save
```bash
printf '%s\n' '{"prompt":"an astronaut cat in neon","options":{"aspect_ratio":"1:1"}}' > request.json
python3 scripts/client.py run generate --payload request.json --state image-state.json --output out.png
```

**Params:**
- `prompt` (string, required) — generation prompt. FLUX understands **English only**.
  - Russian prompts are **auto-translated RU→EN**.
  - Set `translate: false` to disable auto-translation.
- `options.aspect_ratio` (string, optional) — one of:
  - `1:1` (default) · `9:16` · `16:9` · `4:5` · `3:2` · `5:3` · `3:5`
- `width`, `height`, and `size` are unsupported; use `options.aspect_ratio`.

**Response:**
```json
{"task_uid": "<uuid>"}
```

### Poll status
```bash
# Resume the same provider job only after a timeout or transient polling error.
python3 scripts/client.py resume --state image-state.json --output out.png --timeout 300
```

**Response:**
```text
{"task_uid": "...", "status": "pending | processing | finished | failed", ...}
```

**Polling interval:** every 2 seconds, for up to 120 seconds by default; pass
`--timeout SECONDS` to wait longer. GPU queue may occasionally stall.

### Download result
`run` and `resume` download `GET /v1/images/tasks/{uid}/result` only after
`status=finished`. On failure or timeout they leave no new result artifact.

Returns the PNG image as raw binary.

---

## 2. Upscale ×4

```bash
python3 scripts/client.py run upscale --file photo.jpg --state upscale-state.json --output photo-upscaled.png
```

Submit as **multipart/form-data** with `image=@<filename>`.

---

## 3. Background Removal

```bash
python3 scripts/client.py run background/remove --file portrait.png --state background-state.json --output transparent.png
```

---

## 4. Image Enhancement

```bash
python3 scripts/client.py run enhance --file photo.jpg --state enhance-state.json --output enhanced.png
```

All processing examples use the documented multipart `image` field. Each POST returns a task ID, not image bytes; the helper polls and then downloads the binary result.

---

## 5. Avatar Generation

```bash
python3 scripts/client.py run avatar --file selfie.jpg --state avatar-state.json --output avatar.png
```

---

## 6. Quota Check

```bash
python3 scripts/client.py check generate
```

Verified quota structure: top-level `tier`, with `img.day.remaining` and
`img.month.remaining`. Both windows must cover one operation.

---

## Complete Python Example: Generate + Poll + Save

```python
import json
from pathlib import Path
import subprocess
Path("request.json").write_text(json.dumps({"prompt": "an astronaut cat in neon",
                                         "options": {"aspect_ratio": "1:1"}}))
subprocess.run(["python3", "scripts/client.py", "run", "generate", "--payload", "request.json",
                "--state", "python-image-state.json", "--output", "out.png"], check=True)
# out.png exists as a new artifact only after successful polling and download.
```

---

## Cost & Limits

- Counted in **operations** (1 operation = 1 API call).
- Available on **all tariffs** (free, starter, pro).
- Quota endpoint returns remaining ops.
- Status + result downloads do **not** consume quota.

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
  Key 1 of NEURALDEEP_API_KEY pays from the wallet, not a subscription: about 4.00 RUB
  (1 x 4 RUB for image:generate), wallet balance 370.05 RUB. Ask the user whether to pay;
  only after a clear yes, run again with --wallet-limit 4.00
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
python3 scripts/client.py check generate
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
| `401` | Key invalid or revoked, or not subscribed to the model | Ask the user to check the key in `NEURALDEEP_IMAGES_API_KEY` (or `NEURALDEEP_API_KEY`) in the environment or `~/.coddy/.env`; never read the file yourself |
| `408` | Upstream timeout after the provider's own retries | Reconcile a submission; resume a job |
| `422` | A parameter outside the allowed values | Fix the parameter |
| `429` | A quota or rate limit; `X-Window` names the session or week window and `Retry-After` the wait | Check the quota with `check`; wait, then decide explicitly |
| `500` | Internal error; the provider suggests repeating | Reconcile a submission before any new one; resume a job |
| `502` | Upstream unavailable; usually passes on its own | Reconcile or resume as above |
| `503` | Temporarily unavailable, with `Retry-After` | Wait; reconcile or resume as above |

Any other status is reported as `HTTP <code>` without a hint. A transport
failure or an unreadable answer is `Transport or response error`, with the same
outcomes.

- The generation queue may stall: keep a polling timeout and resume the same job.

## Privacy & Security

- Do not upload personal or sensitive images without user consent.
- Prompts leave the local machine; avoid including private data.
- Generated images are stored temporarily; download promptly.
