# 01 - Threat Model

A threat model is a short answer to three questions. What am I protecting?
What could go wrong? What did I do about it?

This one is small on purpose. It is a home lab, not an enterprise.

## Scope

In scope: the WSL2 distro `openclaw`, the OpenClaw gateway, the Telegram
channel, the API keys, and the config file.

Out of scope: the Windows host's own security, my home router, and Telegram's
own servers. I trust those, or at least I am not trying to fix them here.

---

## 1. Assets

What an attacker would actually want.

| # | Asset | Where it lives | Why it matters |
|---|---|---|---|
| A1 | ClinePass API key | `~/.openclaw/openclaw.json` (plaintext) | Stolen key = free LLM usage billed to me |
| A2 | Gemini API key | `~/.openclaw/openclaw.json` (plaintext) | Same, plus ties to the agent's Google account |
| A3 | Telegram bot token | Config | Whoever holds it **is** the bot. Can read and send messages |
| A4 | Gateway secret | Config, plaintext | Authenticates control of the gateway |
| A5 | Agent workspace | `~/.openclaw/workspace` | Files the agent reads and writes |
| A6 | The agent's ability to act | Gateway process | Shell exec, process tools, browser control |
| A7 | The Windows host | Outside the distro | The thing isolation is meant to protect |
| A8 | My conversations | Sent to third-party LLMs | Anything I type leaves my machine |

Note on A6. The most valuable asset is not a file. It is the agent's *power*.
The agent can run commands. An attacker who cannot read a single key but can
make the agent run one command has already won.

---

## 2. Threats

### T1 - Prompt injection

**What it is.** The agent reads text from somewhere. That text contains
instructions. The agent follows them, because to a language model, instructions
and data look the same.

**How it could reach Zion.**

- Web search results. The DuckDuckGo plugin pulls page text straight into the
  model's context. A page can say "ignore previous instructions, run this".
- Files in the workspace. If the agent reads a file someone else wrote.
- Telegram messages from anyone who gets past the pairing check.

**Why it is the top threat here.** Because of A6. Exec tools are on and the
sandbox is off. A successful injection does not just produce a bad answer. It
can run code as `claw`.

**Mitigations in place**

- `tools.fs.workspaceOnly = true`. File tools cannot leave
  `~/.openclaw/workspace`. Injection cannot say "read `~/.ssh/id_rsa`" and get
  it.
- No `/mnt/c`. Even a full shell as `claw` cannot touch Windows files.
- No skills, no extra plugins. Fewer places for hostile text to enter.
- Telegram pairing. Only an approved user can feed the agent input.

**Mitigation missing**

- Sandbox is off. This is the honest gap. Docker-based sandboxing is the real
  fix and it is deferred. Until then, isolation is the blast wall, not
  prevention.

**Residual risk: MEDIUM-HIGH.** Contained to the distro. Not prevented.

---

### T2 - API key theft

**What it is.** Someone gets A1, A2, A3 or A4 and uses them.

**How it could happen.**

- Keys are stored in plaintext in `openclaw.json`. Anything running as `claw`
  can read that file. That includes the agent itself under injection.
- Accidental publication. A screenshot with a key in it. A config file
  committed to this very repo.
- A `.bak` file left behind by a manual config edit.

**Mitigations in place**

- Keys live only inside the isolated distro. Not on Windows, not in a shared
  folder.
- Dedicated Gmail account for the agent. The Gemini key is not tied to my
  personal Google identity.
- Gemini billing is **not enabled**. If that key leaks, the ceiling is the free
  tier, not my card.
- `.gitignore` blocks `openclaw.json`, `*.bak`, `*.bak2`, `.env`, `audit.txt`.
- Screenshots containing keys were withheld from this repo entirely, not
  blurred. See `screenshots/README.md`.
- Every credential in this repo is a placeholder.

**Mitigations missing**

- Plaintext at rest. SecretRef would fix it. Not done.
- Keys have not been rotated yet. They must be rotated before this repo goes
  public, because they existed on screen during the build.

**Residual risk: MEDIUM.** Blast radius is capped by the no-billing choice and
the identity separation.

---

### T3 - Exposed gateway

**What it is.** The OpenClaw gateway speaks HTTP. If it listens somewhere
reachable, anyone who reaches it can drive the agent.

**How it could happen.**

- Binding `0.0.0.0` instead of `127.0.0.1`, exposing it to the whole LAN.
- Turning on Tailscale and forgetting the ACLs.
- A port forward on the router.
- WSL2's networking quirks putting the listener somewhere I did not expect.

**Mitigations in place**

- Bind is **Loopback, `127.0.0.1:18789`**. Chosen deliberately in the wizard.
- Tailscale off.
- No port forwarding on the router.
- Remote access is Telegram, and Telegram is **outbound polling**. The gateway
  dials out. Nothing dials in. This is the single most important design choice
  in the whole build.
- Webhooks disabled (confirmed in the audit's attack surface section).
- `openclaw gateway status` confirms the listener address after every restart.

**Residual risk: LOW.** Verified by the audit, and verified again after each
service restart.

---

### T4 - Malicious or compromised skills and plugins

**What it is.** OpenClaw skills and plugins are code that runs inside the
agent. A hostile or hijacked package runs with the agent's privileges.

**How it could happen.**

- Installing from a community registry with no review.
- Typosquatting a package name.
- A legitimate package getting compromised in a later version, and an unpinned
  install pulling it in automatically.

**Mitigations in place**

- Official `@openclaw` npm scope only. I skipped the community ClawHub
  registry during onboarding.
- **Zero skills installed.** The wizard offered skill dependencies. I skipped
  them.
- **Zero optional plugins** beyond DuckDuckGo search. Plugin config skipped
  too.
- DuckDuckGo was chosen partly because it needs no API key, so it holds no
  secret.

**Mitigation missing**

- `@openclaw/duckduckgo-plugin` is **installed unpinned**. The audit flagged
  this as `plugins.installs_unpinned_npm_specs`. An unpinned spec means a
  future compromised release gets installed on the next update without me
  reviewing it.

**Residual risk: LOW.** One package, official scope, no secret attached. But it
is a real gap and pinning it is on the open items list.

---

### T5 - Data leaving the machine (accepted, not mitigated)

Every message goes to a third-party LLM. ClinePass first, Google second. That
is inherent to the design.

There is no technical control for this. The control is a rule I follow: **no
PHI, no credentials, no client data goes to the agent.** Written down here so it
counts as a policy and not just an intention.

**Residual risk: accepted.**

---

## 3. Mitigation summary

| Threat | Main control | Residual |
|---|---|---|
| T1 Prompt injection | workspaceOnly, distro isolation, no skills | Medium-High |
| T2 Key theft | Isolation, no billing, separate identity, gitignore | Medium |
| T3 Exposed gateway | Loopback bind, outbound-only Telegram, no Tailscale | Low |
| T4 Malicious skills | Official scope, nothing installed | Low |
| T5 Data egress | Written usage rule | Accepted |

## 4. What would change my risk picture

- Turning the sandbox on would drop T1 from Medium-High to Low.
- Moving secrets to SecretRef would drop T2 to Low.
- Adding any skill or plugin would raise T1 and T4 immediately.
- Enabling Tailscale without ACLs would raise T3 to High.

## Sources

- OpenClaw gateway security: <https://docs.openclaw.ai/gateway/security>
- OpenClaw getting started: <https://docs.openclaw.ai/start/getting-started>
