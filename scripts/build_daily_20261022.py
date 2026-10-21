import concurrent.futures
import hashlib
import json
from pathlib import Path
from make_line_contact_sheet import build

PRODUCTS = [
    ("37341318", 24),
    ("37341306", 24),
    ("37341297", 24),
    ("37341290", 16),
    ("37323397", 16),
    ("37323393", 24),
    ("37323392", 16),
    ("37313252", 16),
    ("37300209", 24),
    ("37300174", 16),
]

def one(product):
    sticker_id, count = product
    target = Path("stamps") / f"daily-20261022-{sticker_id}.jpg"
    if not target.exists():
        build(sticker_id, count, target, "ネタさま")

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(one, PRODUCTS))

entries = []
for sticker_id, count in PRODUCTS:
    target = Path("stamps") / f"daily-20261022-{sticker_id}.jpg"
    entries.append({
        "sticker_id": sticker_id,
        "count": count,
        "path": str(target),
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "size": target.stat().st_size,
    })
manifest = Path("manifests/daily-20261022.json")
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps({"date": "2026-10-22", "products": entries}, ensure_ascii=False, indent=2) + "\n")
