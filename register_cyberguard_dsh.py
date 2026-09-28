#!/usr/bin/env python3
"""register_cyberguard_dsh.py — make the fine-tuned cyber model selectable in DSH.

Registers a provider entry in ~/.dsh/settings.yaml so the model appears in the model picker.
This is the part of "create a space with the model selected" that is actually programmatic:
DSH sessions are created by the web app on first use and keyed by working directory, so there
is no supported way to fabricate one — but a registered model IS selectable in a space the
moment that space is created.

Safety, because this file configures the harness that is running this very session:
  * takes a timestamped backup before writing
  * parses and re-parses with PyYAML, and refuses to write if the round-trip differs
  * writes atomically (temp file + rename)
  * idempotent — re-running updates the entry in place rather than duplicating it
  * touches nothing else: it does NOT change agent-default-model or subagent-model-selection

Usage:
  register_cyberguard_dsh.py [--port 18081] [--model-id cyberguard-4b] [--remove]
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import shutil
import sys
from pathlib import Path

import yaml

SETTINGS = Path.home() / ".dsh" / "settings.yaml"
PROVIDER_KEY = "cyberguard-local"


def entry(port: int, model_id: str, display: str) -> dict:
    return {
        "displayName": display,
        "api": "openai-completions",
        "baseURL": f"http://127.0.0.1:{port}/v1",
        "compat": {"supportsDeveloperRole": False, "maxTokensField": "max_tokens"},
        "headers": {"Authorization": "Bearer dummy"},
        "models": [
            {
                "id": model_id,
                "name": "CyberGuard 4B (fine-tuned cyber defence)",
                "contextWindow": 8192,
                "maxTokens": 2048,
            }
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=18081)
    ap.add_argument("--model-id", default="cyberguard-4b")
    ap.add_argument("--display", default="Local cyber-defence model (cyberguard)")
    ap.add_argument("--remove", action="store_true", help="unregister instead of register")
    a = ap.parse_args()

    if not SETTINGS.exists():
        print(f"REFUSED: {SETTINGS} not found")
        return 1

    original_text = SETTINGS.read_text()
    doc = yaml.safe_load(original_text)
    if not isinstance(doc, dict):
        print("REFUSED: settings.yaml did not parse to a mapping")
        return 1

    before = copy.deepcopy(doc)
    providers = doc.setdefault("llm-pi-ai", {}).setdefault("providers", {})
    if not isinstance(providers, dict):
        print("REFUSED: llm-pi-ai.providers is not a mapping")
        return 1

    if a.remove:
        providers.pop(PROVIDER_KEY, None)
        action = "removed"
    else:
        providers[PROVIDER_KEY] = entry(a.port, a.model_id, a.display)
        action = "registered"

    # --- validate the round trip before touching the real file ---
    rendered = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100)
    reparsed = yaml.safe_load(rendered)
    if reparsed != doc:
        print("REFUSED: YAML round-trip is not stable; not writing")
        return 1

    # --- what else would change? (top-level keys must be identical) ---
    if set(reparsed) != set(before):
        print("REFUSED: top-level keys changed; not writing")
        return 1

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = SETTINGS.with_name(f"settings.yaml.bak-cyberguard-{stamp}")
    shutil.copy2(SETTINGS, backup)

    tmp = SETTINGS.with_suffix(".yaml.tmp")
    tmp.write_text(rendered)
    tmp.replace(SETTINGS)

    # --- confirm it still parses from disk ---
    check = yaml.safe_load(SETTINGS.read_text())
    ok = isinstance(check, dict) and PROVIDER_KEY in (check.get("llm-pi-ai", {}).get("providers") or {})
    if not a.remove and not ok:
        print("ERROR: wrote the file but the provider is not visible; restoring backup")
        shutil.copy2(backup, SETTINGS)
        return 1

    print(f"{action}: {PROVIDER_KEY}")
    print(f"  file:    {SETTINGS}")
    print(f"  backup:  {backup}")
    print(f"  baseURL: {entry(a.port, a.model_id, a.display)['baseURL']}")
    print(f"  model:   {a.model_id}")
    print("  providers now:", ", ".join(sorted((check.get('llm-pi-ai', {}).get('providers') or {}))))
    print("  untouched: agent-default-model, subagent-model-selection")
    return 0


if __name__ == "__main__":
    sys.exit(main())
