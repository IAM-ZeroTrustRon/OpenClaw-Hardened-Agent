#!/usr/bin/env python3
"""
add-clinepass-provider.py

Adds the ClinePass provider to ~/.openclaw/openclaw.json and makes it the
primary model, with Gemini as the fallback.

Why this script exists
----------------------
The Gemini free tier could not keep up with agent-sized requests (large system
prompt plus tool list on every turn -> instant 429). ClinePass became primary.
See docs/02-build-guide.md step 6.

Secrets
-------
The API key is read from the CLINEPASS_API_KEY environment variable.
It is never hardcoded, and it is never accepted as a command-line argument,
because command lines end up in shell history and in the process list.

If the variable is not set, the script prints a clear message and exits
without touching anything.

Usage
-----
    export CLINEPASS_API_KEY='<CLINEPASS_API_KEY>'
    python3 scripts/add-clinepass-provider.py

Then restart the gateway and confirm:

    systemctl --user restart openclaw-gateway.service
    openclaw models status
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"

PROVIDER_ID = "clinepass"
BASE_URL = "https://api.cline.bot/api/v1"
API_STYLE = "openai-completions"
MODEL_ID = "cline-pass/qwen3.7-max"
CONTEXT_WINDOW = 128000
MAX_TOKENS = 8192

PRIMARY_MODEL = f"{PROVIDER_ID}/{MODEL_ID}"
FALLBACK_MODEL = "google/gemini-3.8-flash"

ENV_VAR = "CLINEPASS_API_KEY"


def fail(message):
    """Print an error and stop. Nothing is written on failure."""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def read_api_key():
    """Read the API key from the environment. Never from a literal."""
    key = os.environ.get(ENV_VAR)

    if key is None:
        fail(
            f"{ENV_VAR} is not set.\n\n"
            f"  This script will not run without it, and the key is never\n"
            f"  hardcoded in this file.\n\n"
            f"  Set it first:\n"
            f"      export {ENV_VAR}='<CLINEPASS_API_KEY>'\n\n"
            f"  Then run this script again. Nothing has been changed."
        )

    key = key.strip()

    if not key:
        fail(
            f"{ENV_VAR} is set but empty.\n"
            f"  Nothing has been changed."
        )

    if key.startswith("<") and key.endswith(">"):
        fail(
            f"{ENV_VAR} still contains the placeholder value {key!r}.\n"
            f"  Replace it with your real key.\n"
            f"  Nothing has been changed."
        )

    return key


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

    The backup contains plaintext keys. '*.bak' is in .gitignore for that
    reason. Never commit one.
    """
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".{stamp}.bak")

    try:
        shutil.copy2(path, backup_path)
    except OSError as exc:
        fail(f"Could not create backup: {exc}")

    print(f"Backup written: {backup_path}")
    return backup_path


def apply_changes(config, api_key):
    """Add the provider and repoint the default model."""
    providers = config.setdefault("providers", {})

    providers[PROVIDER_ID] = {
        "baseUrl": BASE_URL,
        "api": API_STYLE,
        "apiKey": api_key,
        "models": {
            MODEL_ID: {
                "contextWindow": CONTEXT_WINDOW,
                "maxTokens": MAX_TOKENS,
            }
        },
    }

    model_cfg = (
        config.setdefault("agents", {})
        .setdefault("defaults", {})
        .setdefault("model", {})
    )
    model_cfg["primary"] = PRIMARY_MODEL
    model_cfg["fallback"] = FALLBACK_MODEL

    return config


def write_config(path, config):
    """Write atomically, and keep the file readable by its owner only."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")

    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)
            handle.write("\n")

        # 0600. This file holds plaintext API keys.
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, path)
    except OSError as exc:
        tmp_path.unlink(missing_ok=True)
        fail(f"Could not write {path}: {exc}")


def main():
    api_key = read_api_key()

    print(f"Config: {CONFIG_PATH}")
    config = load_config(CONFIG_PATH)
    back_up(CONFIG_PATH)

    config = apply_changes(config, api_key)
    write_config(CONFIG_PATH, config)

    # Never print the key itself.
    print("")
    print("Done.")
    print(f"  Provider added : {PROVIDER_ID} -> {BASE_URL}")
    print(f"  API style      : {API_STYLE}")
    print(f"  Model          : {MODEL_ID}")
    print(f"  Context window : {CONTEXT_WINDOW}")
    print(f"  Max tokens     : {MAX_TOKENS}")
    print(f"  Primary        : {PRIMARY_MODEL}")
    print(f"  Fallback       : {FALLBACK_MODEL}")
    print(f"  API key        : read from ${ENV_VAR} (not shown, not logged)")
    print("")
    print("Next:")
    print("  systemctl --user restart openclaw-gateway.service")
    print("  openclaw models status")


if __name__ == "__main__":
    main()
