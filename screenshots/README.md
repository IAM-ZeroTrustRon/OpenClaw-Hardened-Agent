# Screenshots

This folder is mostly empty on purpose.

## What was withheld

Screenshots of the following build steps are **not in this repo**:

- The ClinePass API key, in AI Studio, in the terminal, and in the config file
- The Gemini API key, in AI Studio and in the config file
- The Telegram bot token from `@BotFather`
- My Telegram user ID
- The pairing code from `openclaw pairing list telegram`
- The generated gateway secret
- Full, unredacted `~/.openclaw/openclaw.json`
- Full, unredacted `openclaw security audit` output

## Why they were withheld and not blurred

Blurring is the obvious answer. I did not use it.

A blur can fail. It can be reversed on a low-entropy string. It can be applied
to the wrong region. It can be flattened incorrectly. It can leave the original
pixels in the file's metadata or in an undo layer. And on a compressed image,
partial characters can sometimes still be recovered from the edges of the
blurred area.

A blur can also simply be forgotten on one image out of twenty. That is the
realistic failure, and it is the one that matters.

**A failed redaction in a public security portfolio is worse than a missing
image.** A missing image costs the reader a little context. A failed redaction
publishes a live credential and, worse, demonstrates that the author's redaction
process does not work — in a document whose whole purpose is to show that the
author handles credentials carefully.

So the rule I applied was: **if an image contains a secret, the image does not
go in the repo.** No blurring, no cropping, no black boxes. Withheld entirely.

This is the same logic as `.gitignore`. That file excludes `openclaw.json`,
`*.bak`, `*.bak2`, `.env`, `audit.txt`, and any screenshot whose filename
contains `SECRET` or `SENSITIVE`. Exclusion beats sanitisation, because
exclusion has no partial-failure mode.

## What is here instead

The written documentation carries the detail the screenshots would have.

- Exact commands, in [`docs/02-build-guide.md`](../docs/02-build-guide.md)
- Every wizard choice and the reason for it, same file
- Audit findings and control mapping, in
  [`docs/04-audit-results.md`](../docs/04-audit-results.md)
- The config structure, with placeholders, in
  [`config/openclaw.example.json5`](../config/openclaw.example.json5)

Nothing important is lost. A screenshot of a terminal is a worse artefact than
the command itself, because you cannot copy it, search it, or diff it.

## Naming convention

If a screenshot is ever added here, any file holding sensitive content must
have `SECRET` or `SENSITIVE` in its filename. `.gitignore` blocks both
patterns, so the file is excluded even if someone stages everything with
`git add -A`.

That is a safety net, not the primary control. The primary control is not
taking the screenshot into the repo folder in the first place.

## Related open item

The ClinePass and Gemini keys **must be rotated before this repo is made
public.** They were visible on screen and in terminal scrollback during the
build. Withholding the images reduces the risk of publication. It does not undo
the exposure that already happened locally.

Tracked as a **High** priority item in
[`docs/03-hardening.md`](../docs/03-hardening.md).
