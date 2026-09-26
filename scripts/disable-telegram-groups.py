#!/usr/bin/env python3
"""
disable-telegram-groups.py

Hardening Fix 2. Removes the Telegram group allowlist and explicitly disables
group access.

The problem
-----------
The onboarding wizard wrote this into the Telegram channel config:

    "groups": { "*": { "requireMention": true } }

"*" is a wildcard. It meant ANY Telegram group the bot was added to could use
the agent. Other people can add a bot to a group. So the effective access
control was "whoever can add my bot to a group".

"requireMention": true is not a security control. It stops the bot replying to
every message in a busy group. It does not stop an unauthorised person using
it.

This also triggered the audit warning
security.trust_model.multi_user_heuristic - OpenClaw noticed the deployment had
quietly become multi-user.

The fix
-------
1. Remove the "groups" block entirely.       -> deletes the permission
2. Set "groupPolicy": "disabled".            -> states the intent explicitly

Both, not one. Removing the block alone leaves no record of the decision, and
a future wizard run or config edit could re-add an entry. An explicit deny
makes the intent part of the config.

Direct messages from the paired account are NOT affected.

Usage
-----
    python3 scripts/disable-telegram-groups.py
    systemctl --user restart openclaw-gateway.service

Then send the bot a DM from the paired account to confirm DMs still work.

Secrets
-------
This script needs no credentials. It does not read, print, or log any key.
It leaves the existing bot token in place untouched.
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"


def fail(message):
    """Print an error and stop. Nothing is written on failure."""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def load_config(path):
    if not path.exists():
        fail(
            f"Config not found at {path}\n"
            f"  Run 'openclaw onboard --classic' first."
        )

    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        fail(f"Could not parse {path} as JSON: {exc}")
    except OSError as exc:
        fail(f"Could not read {path}: {exc}")


def back_up(path):
    """Copy the config aside before editing it.

    The backup contains plaintext keys and the bot token. '*.bak' and '*.bak2'
    are in .gitignore for that reason. Never commit one.
    """
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".{stamp}.bak2")

    try:
        shutil.copy2(path, backup_path)
    except OSError as exc:
        fail(f"Could not create backup: {exc}")

    print(f"Backup written: {backup_path}")
    return backup_path


def find_telegram(config):
    """Locate the Telegram channel config."""
    channels = config.get("channels")

    if not isinstance(channels, dict) or "telegram" not in channels:
        fail(
            "No Telegram channel found in the config.\n"
            "  Nothing has been changed."
        )

    telegram = channels["telegram"]

    if not isinstance(telegram, dict):
        fail(
            "The Telegram channel config is not an object.\n"
            "  Nothing has been changed."
        )

    return telegram


def apply_fix(telegram):
    """Remove the allowlist, set an explicit deny. Returns a change summary."""
    changes = []

    removed = telegram.pop("groups", None)
    if removed is None:
        print("Note: no 'groups' block was present. Nothing to remove.")
    else:
        # Show what was there, without dumping the whole structure.
        keys = list(removed) if isinstance(removed, dict) else [str(removed)]
        print(f"Removed 'groups' allowlist. Entries were: {keys}")
        if "*" in keys:
            print("  That included the wildcard '*' - any group could use the bot.")
        changes.append("removed groups allowlist")

    previous_policy = telegram.get("groupPolicy")
    if previous_policy == "disabled":
        print("Note: groupPolicy was already 'disabled'.")
    else:
        telegram["groupPolicy"] = "disabled"
        print(f"Set groupPolicy: {previous_policy!r} -> 'disabled'")
        changes.append("set groupPolicy=disabled")

    return changes


def write_config(path, config):
    """Write atomically, and keep the file readable by its owner only."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")

    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)
            handle.write("\n")

        # 0600. This file holds plaintext API keys and the bot token.
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, path)
    except OSError as exc:
        tmp_path.unlink(missing_ok=True)
        fail(f"Could not write {path}: {exc}")


def main():
    print(f"Config: {CONFIG_PATH}")
    config = load_config(CONFIG_PATH)
    telegram = find_telegram(config)

    back_up(CONFIG_PATH)
    changes = apply_fix(telegram)

    if not changes:
        print("\nConfig was already hardened. No write needed.")
        return

    write_config(CONFIG_PATH, config)

    print("")
    print("Done. Telegram group access is disabled.")
    print("Direct messages from paired accounts are unaffected.")
    print("")
    print("Next:")
    print("  systemctl --user restart openclaw-gateway.service")
    print("  openclaw gateway status")
    print("  Send the bot a DM from the paired account to confirm.")
    print("")
    print("Then re-run the audit - this is still an open item:")
    print("  openclaw security audit > ~/audit.txt 2>&1")


if __name__ == "__main__":
    main()
