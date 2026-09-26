# 02 - Build Guide

How Zion was built, in order. Every command here is one I actually ran.

Target: OpenClaw 2026.9.6, in its own WSL2 distro, on Windows 11, reachable
from Telegram and nowhere else.

Rough time: an afternoon, plus a detour when the free Gemini tier gave up.

---

## Step 1 - Create the isolated WSL2 distro

I already had Ubuntu and kali distros for daily use. The agent does not go in
either of them. It gets its own.

In **PowerShell on Windows**:

```powershell
wsl --update
wsl --install Ubuntu-24.04 --name openclaw
```

The `--name` flag is the whole point. It makes a separate distro with a
separate filesystem.

Then create the dedicated Linux user `claw` inside it, and write
`/etc/wsl.conf`. The full file is in [`config/wsl.conf`](../config/wsl.conf).

The important parts:

```ini
[boot]
systemd=true

[automount]
enabled=false

[interop]
enabled=false
appendWindowsPath=false

[user]
default=claw
```

What each line does:

- `systemd=true` - needed so the gateway can run as a systemd user service.
- `automount enabled=false` - **Windows drives are not mounted.** No `/mnt/c`.
  The agent physically cannot see my Windows files.
- `interop enabled=false` - Linux cannot launch Windows `.exe` files.
- `appendWindowsPath=false` - Windows directories are not added to `PATH`.
  Without this, `interop=false` is half a control, because the PATH still
  points at Windows binaries.
- `default=claw` - shells open as the dedicated user, not root.

### Verify it (do not skip this)

`wsl.conf` is read at boot, so the distro has to be restarted first.

```bash
wsl --terminate openclaw
wsl -d openclaw
```

Then inside the distro:

```bash
ls /mnt/c     # expect: nothing. No such directory, or empty.
whoami        # expect: claw
```

If `ls /mnt/c` lists your Windows drive, the config did not take effect. Stop
and fix it. This check is the difference between an isolated agent and an agent
that can read `C:\Users\`.

---

## Step 2 - Base setup and accounts

Update the system:

```bash
sudo apt update && sudo apt upgrade -y
```

Then three accounts, all separate from my personal ones:

1. **A dedicated Gmail account for the agent.** Not my personal email. If the
   agent's identity gets abused, it is not my identity.
2. **A Gemini API key**, created in Google AI Studio while signed in as that
   new account. **Billing was not enabled.** If this key leaks, the worst case
   is free tier exhaustion, not a bill.
3. **A Telegram bot**, created with `@BotFather`. Keep the token
   (`<TELEGRAM_BOT_TOKEN>`) somewhere safe. It is a credential, not a name.

---

## Step 3 - Install OpenClaw and run onboarding

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
source ~/.bashrc
openclaw --version
```

`source ~/.bashrc` matters. Without it the shell has not picked up
`~/.npm-global/bin` yet and you get "command not found". See lesson 3.

Then the wizard:

```bash
openclaw onboard --classic
```

### Choices I made, and why

| Prompt | Choice | Reason |
|---|---|---|
| Setup type | Manual setup | I want to see every option, not accept defaults |
| Gateway | Local gateway | No cloud relay |
| Default model | `google/gemini-3.8-flash` | Free to start. Changed later, see step 6 |
| Port | 18789 | Default |
| Bind address | **Loopback `127.0.0.1`** | Not LAN, not `0.0.0.0`. The key security choice |
| Tailscale | Off | No remote network path at all |
| Gateway secret | Generated | Stored plaintext. Known gap, SecretRef is the fix |
| Live AI test | Yes | Confirms the key works before going further |
| Channel | **Telegram** | Discord webhooks are one-way, so a Discord bot would be extra work |
| DM policy | **Pairing** | Strangers cannot message the agent |
| Operator account | Skipped | Not needed for a single user |
| Search | DuckDuckGo | No API key, so no extra secret to protect |
| npm scope | **Official `@openclaw`** | Not community ClawHub. Supply chain |
| Skill dependencies | Skipped | Least privilege |
| Optional plugins | Skipped | Least privilege |
| Plugin config | Skipped | Least privilege |
| systemd lingering | **Enabled** | Service survives me logging out |

The three "skipped" rows are deliberate. Every skill and plugin is code running
with the agent's privileges. I started with none and will add only what I can
justify.

### The wizard hung

At "Preparing gateway service", the wizard stopped and never finished. This
appears to be a known rough edge. I exited and installed the service by hand.

---

## Step 4 - Install the gateway service manually

```bash
openclaw gateway install
openclaw gateway status
```

The first `status` call may look wrong. Give it about **30 seconds** to warm
up. Then you should see the probe report `ok` and the listener on
`127.0.0.1:18789`.

Confirm the address every time. A gateway on `0.0.0.0` is a different product.

---

## Step 5 - Pair Telegram

Message the bot from your phone first. That creates a pending pairing request.
Then, in the distro:

```bash
openclaw pairing list telegram
openclaw pairing approve telegram <PAIRING_CODE>
```

Now only the approved account can talk to the agent. Anyone else who finds the
bot gets nothing.

The pairing code and my Telegram user ID are both sensitive, which is why the
screenshots of this step are not in the repo.

---

## Step 6 - Swap the primary model to ClinePass

Gemini's free tier kept returning HTTP 429. Not occasionally. Immediately, on
the first real turn. Details in lesson 1.

So ClinePass became the primary and Gemini dropped to fallback.

### Test the key first, outside OpenClaw

Always prove a credential works before you wire it into anything:

```bash
export CLINEPASS_API_KEY='<CLINEPASS_API_KEY>'

curl -sS https://api.cline.bot/api/v1/chat/completions \
  -H "Authorization: Bearer $CLINEPASS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "model": "cline-pass/qwen3.7-max",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 16
      }'
```

A normal completion back means the key and endpoint are good. If OpenClaw then
fails, the problem is OpenClaw's config, not the key. That split saves a lot of
guessing.

### Back up the config before editing it

```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak
```

Note: `*.bak` is in `.gitignore`. Backups of a config full of plaintext keys
must never be committed.

### Add the provider

Run the helper script:

```bash
export CLINEPASS_API_KEY='<CLINEPASS_API_KEY>'
python3 scripts/add-clinepass-provider.py
```

The script reads the key from the environment. It does not accept a key on the
command line, because command lines end up in shell history. If
`CLINEPASS_API_KEY` is not set, it exits with a clear message and changes
nothing.

What it writes:

```
provider id     clinepass
baseUrl         https://api.cline.bot/api/v1
api             openai-completions
model           cline-pass/qwen3.7-max
contextWindow   128000
maxTokens       8192
```

And it sets:

```
agents.defaults.model.primary   clinepass/cline-pass/qwen3.7-max
agents.defaults.model.fallback  google/gemini-3.8-flash
```

A sanitised version of the whole config is in
[`config/openclaw.example.json5`](../config/openclaw.example.json5).

### Restart and verify

```bash
systemctl --user restart openclaw-gateway.service
openclaw models status
```

`models status` should show ClinePass primary and Gemini fallback.

---

## Step 7 - Harden

This is its own document. See [03-hardening.md](03-hardening.md).

Short version: run `openclaw security audit`, then fix what it finds.

---

## Everyday operation

WSL2 shuts a distro down when it is idle. The agent stops answering Telegram
and nothing appears to be wrong.

Wake it:

```powershell
wsl -d openclaw
```

Lingering keeps the service running once the distro is up. It does not keep the
distro itself alive. See lesson 7.

## Sources

- <https://docs.openclaw.ai/start/getting-started>
- <https://docs.openclaw.ai/platforms/windows>
- <https://docs.openclaw.ai/concepts/models>
- <https://docs.openclaw.ai/concepts/model-providers/custom-providers>
- <https://docs.cline.bot/getting-started/clinepass>
