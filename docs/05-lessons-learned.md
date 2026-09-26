# 05 - Lessons Learned

Seven things that cost me time or changed how I think about this.

---

## 1. A free API tier is not an agent tier

The Gemini free tier key worked perfectly in a `curl` test. Wired into
OpenClaw, it returned **429 RESOURCE_EXHAUSTED** almost immediately.

**Why.** A chat app sends a short message. An agent sends a large system
prompt plus a full tool list **on every single turn**. The token cost per turn
is an order of magnitude higher. A quota sized for casual chat is gone in a
handful of agent turns.

There is no free quota on Gemini Pro models either, so upgrading the model was
not a way out.

**What I do now.** Test a key with a realistic payload, not a one-word ping. A
successful `curl` proves the credential is valid. It proves nothing about
whether the quota survives real use.

This is the lesson that reshaped the build. It is why ClinePass became primary.

---

## 2. Key formats change, and that is fine

The AI Studio key started with `AQ.` — not the `AIza` prefix I expected.

I assumed it was broken or truncated. It was neither. It worked.

**Lesson.** Do not judge a credential by its prefix. Test it.

---

## 3. PATH problems look like install failures

After the install script finished, `openclaw --version` gave
"command not found".

The install had succeeded. `~/.npm-global/bin` was simply not in the current
shell's `PATH` yet, because the shell had started before `~/.bashrc` was
modified.

```bash
source ~/.bashrc
```

Fixed instantly.

**The trap.** Ubuntu's `command-not-found` helper suggested
`sudo snap install openclaw`. I ignored it. That is not the official
distribution channel. Installing the wrong package because a shell hint
suggested it is a small decision with supply chain consequences.

**Lesson.** "Command not found" right after a successful install is almost
always PATH. And never take a package suggestion from a shell error message at
face value.

---

## 4. The wizard hangs on the gateway service

`openclaw onboard --classic` stopped at **"Preparing gateway service"** and
never moved.

Nothing was broken. I exited and did it by hand:

```bash
openclaw gateway install
openclaw gateway status
```

The first `status` call also looks wrong. Allow about **30 seconds** of
warm-up, then the probe reports `ok` and the listener shows on
`127.0.0.1:18789`.

**Lesson.** Know the manual equivalent of every wizard step. A wizard is a
convenience wrapper around commands you can run yourself.

---

## 5. Wizard defaults are not least privilege

This is the biggest security lesson in the project.

I chose carefully all the way through onboarding. Loopback bind. No Tailscale.
Skipped skills, plugins and plugin config. Official npm scope.

And I **still** ended up with:

- `tools.fs.workspaceOnly = false` — file tools could roam the whole home
  directory
- Telegram `groups: { "*": { requireMention: true } }` — any group could use my
  bot

Both were defaults. Neither was a choice I made. The audit found both.

**Lesson.** Defaults are tuned for things working, not for things being safe.
Run the security audit after every build, and after every config change. It
took seconds and found two real problems I would not have spotted by reading
the file.

---

## 6. Subscriptions are not API access

I first thought about pointing the agent at a Claude Pro/Max or Gemini app
subscription. Cheaper, apparently.

That does not work, and trying it risks the account.

- **Anthropic blocked subscription use by third-party agents in April 2026.**
  (*The Register*, 6 Apr 2026.)
- **Google has suspended accounts** for driving app subscriptions through
  automated third-party clients.
- **ClinePass explicitly permits API use outside Cline itself**, which is why
  it was a safe fit here.

**Lesson.** Check the terms of service before the price. A subscription buys
you access to a vendor's own client. An API key buys you the right to build on
it. They are different products, and using one as the other can cost you the
account.

---

## 7. WSL2 idles out

The agent stopped answering Telegram. Nothing had crashed. The `openclaw`
distro had simply been shut down by WSL2 for being idle.

```powershell
wsl -d openclaw
```

Wakes it up.

**The nuance.** systemd lingering is enabled, and it does its job — the service
starts without an interactive login and survives me logging out. But lingering
is a *systemd* setting. It has no say over whether *WSL2* keeps the distro
running. Two different layers.

**Lesson.** Know which layer each of your reliability settings actually
controls. This is also why a dedicated always-on box (the Beelink mini PC on
the future list) is the real fix rather than another config flag.

---

## What I would do differently

1. **Run `openclaw security audit` before the first real use**, not after. It
   would have caught both defaults on day one.
2. **Budget the token cost before choosing a model.** I picked on price and got
   sent back to the start.
3. **Re-run the audit immediately after each fix, while the terminal is still
   open.** I did not, and this repo has a "pending" cell as a result.
4. **Decide the sandbox story up front.** "Deferred, needs Docker" is a real
   answer, but it would have been a cheaper decision before the build than
   after.
5. **Plan key rotation as part of the build**, since keys appear in terminals
   and screenshots during setup. Rotating before publication should be a
   scheduled step, not a memory test.

## Sources

- <https://docs.openclaw.ai/start/getting-started>
- <https://docs.openclaw.ai/platforms/windows>
- <https://docs.cline.bot/getting-started/clinepass>
- <https://www.theregister.com/2026/04/06/anthropic_closes_door_on_subscription/>
