#!/usr/bin/env bash
# stage-cap-data.sh — fetch authoritative + labeled data for the capability harness.
# Every fetch is logged; failures are recorded, never faked. CPU-only.
set -uo pipefail
source ~/.cyberguard-env
D="$CYBERGUARD_ROOT/cap"
mkdir -p "$D"/{data,receipts,outputs}
LOG="$CYBERGUARD_ROOT/logs/stage-cap-data.log"
say() { echo "$(date -u +%FT%TZ) $*" >> "$LOG"; }
PY="$CYBERGUARD_VENV/bin/python"

say "stage start"
# 1. MITRE ATT&CK STIX bundle (TID ground truth)
cd "$D/data"
for url in \
  "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/attack-pattern/enterprise-attack.json" \
  "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json"; do
  timeout 300 curl -sfL "$url" -o attack-enterprise.json && { say "attack-stix OK $url size=$(stat -c %s attack-enterprise.json)"; break; }
done
[ -s attack-enterprise.json ] || say "attack-stix FAILED all urls"

# 2. CIEM (cisagov, MIT) — incident reports with gold IOCs
timeout 300 curl -sfL "https://codeload.github.com/cisagov/CIEM/tar.gz/refs/heads/main" -o CIEM.tar.gz \
  && tar xzf CIEM.tar.gz && say "CIEM tar OK" || say "CIEM FAILED"
find "$D/data" -iname "*sciq*" -name "*.json" 2>/dev/null | head -5 >> "$LOG"

# 3. GSM8K subset via HF datasets
$PY - <<'PYX' >> "$LOG" 2>&1
from datasets import load_dataset
import json
ds = load_dataset("openai/gsm8k", "main", split="test")
rows = ds.select(range(0, 120))
with open("/home/clawerdigi2/cyberguard/cap/data/gsm8k-120.json", "w") as f:
    json.dump([{"q": r["question"], "a": r["answer"]} for r in rows], f)
print("gsm8k OK", len(rows))
PYX
[ -s "$D/data/gsm8k-120.json" ] || say "gsm8k FAILED"

# 4. phishing labeled set — try HF candidates in order
$PY - <<'PYX' >> "$LOG" 2>&1
import json
out = "/home/clawerdigi2/cyberguard/cap/data/triage-labeled.json"
tried = []
for name in ["Erika/PhishingEmailsDataset", "burtenshaw/phishing", "Deep-Crawler/phishing-detection"]:
    try:
        from datasets import load_dataset
        ds = load_dataset(name, split="train")
        cols = ds.column_names
        lab_col = next((c for c in cols if c.lower() in ("label", "labels", "class")), None)
        txt_col = next((c for c in cols if c.lower() in ("text", "email", "body", "content", "mail")), None)
        if lab_col is None or txt_col is None:
            tried.append((name, f"no usable cols {cols[:8]}")); continue
        rows, seen = [], set()
        for r in ds:
            t, l = str(r[txt_col] or ""), str(r[lab_col])
            if len(t) < 120 or len(t) > 4000: continue
            key = t[:200]
            if key in seen: continue
            seen.add(key)
            rows.append({"text": t, "label": l})
            if len(rows) >= 240: break
        mal = sum(1 for r in rows if r["label"].lower() in ("1","malicious","phishing","spam"))
        if mal < 40 or len(rows) < 120:
            tried.append((name, f"balance/size unusable: {len(rows)} rows, {mal} malicious")); continue
        json.dump({"source": name, "rows": rows}, open(out, "w"))
        print("triage OK from", name, len(rows), "malicious:", mal); break
    except Exception as e:
        tried.append((name, repr(e)[:120]))
else:
    print("triage FALLBACK needed; tried:", tried)
PYX
[ -s "$D/data/triage-labeled.json" ] || say "triage dataset FAILED -> harness will use documented fallback set"

# 5. pySigma
$CYBERGUARD_VENV/bin/pip install --quiet pySigma >> "$LOG" 2>&1 && say "pysigma install OK" || say "pysigma install FAILED"

# 6. NVD reachability warm-up + key-less rate check
code=$(timeout 20 curl -s -o /dev/null -w "%{http_code}" "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2021-44228")
say "nvd probe http=$code"
say "stage done"
