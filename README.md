# OpenClaw Hardened Agent ("Zion")

[Portfolio index](https://github.com/IAM-ZeroTrustRon/GRC-IAM-Portfolio) · **Repository role:** Personal AI-agent hardening lab.

A personal AI agent, self-hosted and locked down.

This repo documents how I built it, how I hardened it, what the security audit
found, and what is still open. It is a portfolio piece. It is not a product.

## What it is

- Agent name: **Zion**
- Software: **OpenClaw 2026.9.6** (installed from npm)
- Host: Windows 11 machine named **GameChanger**
- Runs inside: a **dedicated WSL2 Ubuntu 24.04 distro** called `openclaw`
- Reachable from: **localhost only** (`127.0.0.1:18789`)
- I talk to it over: **Telegram**

## Why I built it this way

I wanted an agent I could message from my phone. I did not want that to mean
opening a port to the internet, or letting the agent read my whole Windows
drive, or mixing it in with my daily Linux setup.

So the agent lives in its own box. The box has no access to `C:`. The gateway
listens on loopback only. Telegram does the remote part, and Telegram works by
the gateway calling out, not by anything calling in.

## Architecture

```
Phone (Telegram app)
      |
      |  Telegram Bot API  (gateway polls OUTBOUND - nothing dials in)
      v
Windows 11 host "GameChanger"
      |
      v
WSL2 distro "openclaw"        <- C: NOT mounted, Windows interop OFF
      |
      v
Linux user "claw"             <- dedicated, not my personal user
      |
      v
openclaw-gateway.service      <- systemd user service, lingering ON
      |
      +-- listens 127.0.0.1:18789 ONLY
      +-- workspace ~/.openclaw/workspace  (fs.workspaceOnly = true)
      |
      +--> primary LLM   api.cline.bot            (clinepass / cline-pass/qwen3.7-max)
      +--> fallback LLM  generativelanguage.googleapis.com (google/gemini-3.8-flash)
```

## Components

| Piece | Choice | Why |
|---|---|---|
| Isolation | Separate WSL2 distro `openclaw` | Keeps it away from my daily Ubuntu and kali distros |
| OS user | `claw` | Dedicated. No personal files, no personal keys |
| Install | npm, `~/.npm-global` | No root-owned global install |
| Gateway | systemd user service, `127.0.0.1:18789` | No LAN exposure, no public exposure |
| Primary model | `clinepass/cline-pass/qwen3.7-max` | OpenAI-compatible, allows API use outside Cline |
| Fallback model | `google/gemini-3.8-flash` | Free tier, used only as backup |
| Chat channel | Telegram bot, DM policy = **pairing** | Unknown users cannot just message it |
| Search | DuckDuckGo plugin | No API key needed |
| Skills / extra plugins | **None** | Deliberate. Less code = less attack surface |

## Documents

| File | What is in it |
|---|---|
| [docs/01-threat-model.md](docs/01-threat-model.md) | What I am protecting, what could go wrong, what I did about it |
| [docs/02-build-guide.md](docs/02-build-guide.md) | Step-by-step build, with the real commands |
| [docs/03-hardening.md](docs/03-hardening.md) | The two fixes I applied after the audit |
| [docs/04-audit-results.md](docs/04-audit-results.md) | Audit output, control mapping to NIST CSF 2.0 |
| [docs/05-lessons-learned.md](docs/05-lessons-learned.md) | Seven things that surprised me |
| [screenshots/README.md](screenshots/README.md) | Why some screenshots are missing |

## Honest status

This build is not finished, and the docs say so.

**Fixed**

- `tools.fs.workspaceOnly` was `false`. Now `true`.
- Telegram groups were wildcard-allowed (`"*"`). Now `groupPolicy: "disabled"`.

**Still open**

- The audit has **not been re-run** after the second fix. The "after" numbers
  do not exist yet, so this repo does not print any.
- **Secrets sit in plaintext** in `~/.openclaw/openclaw.json`. Inside an
  isolated distro, but still plaintext. SecretRef is the planned fix.
- **Sandbox is off.** Runtime and process tools run unsandboxed. Proper
  sandboxing needs Docker. Deferred, not solved.
- The **DuckDuckGo plugin is unpinned** in npm. Low risk, still a supply chain
  gap.

I would rather name these than imply a clean build. A portfolio piece that
hides its gaps is not a security portfolio piece.

## Secrets policy for this repo

There are no real secrets here. Every credential is a placeholder:

`<CLINEPASS_API_KEY>`, `<GEMINI_API_KEY>`, `<TELEGRAM_BOT_TOKEN>`,
`<TELEGRAM_USER_ID>`

The scripts read keys from environment variables and refuse to run if the
variable is missing. Nothing is hardcoded.

## Sources

- OpenClaw docs: <https://docs.openclaw.ai/> (start/getting-started,
  gateway/security, concepts/models, concepts/model-providers/custom-providers,
  platforms/windows)
- ClinePass: <https://docs.cline.bot/getting-started/clinepass>
- NIST Cybersecurity Framework (CSF) 2.0, NIST CSWP 29:
  <https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf>
- The Register, 6 Apr 2026, on Anthropic closing subscription access to
  third-party agents:
  <https://www.theregister.com/2026/04/06/anthropic_closes_door_on_subscription/>
