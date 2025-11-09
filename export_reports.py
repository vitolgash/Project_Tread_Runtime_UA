
import os, json, csv
from datetime import datetime

ROOT = os.path.abspath(os.path.dirname(__file__))
LOG_PATH = os.path.join(ROOT, "logs")
REPORT_PATH = os.path.join(ROOT, "reports")
os.makedirs(REPORT_PATH, exist_ok=True)
records = []

if os.path.isdir(LOG_PATH):
    for fname in sorted(os.listdir(LOG_PATH)):
        if fname.endswith(".json"):
            with open(os.path.join(LOG_PATH, fname), encoding="utf-8") as f:
                data = json.load(f)
                ts = data.get("timestamp") or fname.replace("log_", "").replace(".json", "")
                for a in data.get("alerts", []):
                    records.append({
                        "timestamp": ts,
                        "category": "Law" if "⚖️" in a else "Sanction" if "🇬🇧" in a or "🇺🇸" in a else "System",
                        "message": a
                    })

summary = {
    "generated_at": datetime.now().isoformat(),
    "total_records": len(records),
    "by_category": {
        "Law": sum(1 for r in records if r["category"] == "Law"),
        "Sanction": sum(1 for r in records if r["category"] == "Sanction"),
        "System": sum(1 for r in records if r["category"] == "System")
    },
    "records": records
}

with open(os.path.join(REPORT_PATH, "summary.json"), "w", encoding="utf-8") as jf:
    json.dump(summary, jf, ensure_ascii=False, indent=2)

with open(os.path.join(REPORT_PATH, "summary.csv"), "w", newline="", encoding="utf-8") as cf:
    writer = csv.DictWriter(cf, fieldnames=["timestamp", "category", "message"])
    writer.writeheader()
    writer.writerows(records)

print(f"[OK] Export complete — {len(records)} records saved.")
