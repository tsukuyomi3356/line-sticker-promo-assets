import concurrent.futures
import hashlib
import json
from pathlib import Path
from make_line_contact_sheet import build

PRODUCTS = [
    ("37480582", 24),
    ("37480572", 16),
    ("37480559", 24),
    ("37480558", 16),
    ("37480543", 16),
    ("37477480", 24),
    ("37472079", 24),
    ("37472090", 24),
    ("37472077", 16),
    ("37015800", 16),
]

def one(product):
    sticker_id, count = product
    target = Path("stamps") / f"daily-20261023-{sticker_id}.jpg"
    if not target.exists():
        build(sticker_id, count, target, "ネタさま")

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(one, PRODUCTS))

entries = []
for sticker_id, count in PRODUCTS:
    target = Path("stamps") / f"daily-20261023-{sticker_id}.jpg"
    entries.append({
        "sticker_id": sticker_id,
        "count": count,
        "path": str(target),
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "size": target.stat().st_size,
    })
manifest = Path("manifests/daily-20261023.json")
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps({"date": "2026-10-23", "products": entries}, ensure_ascii=False, indent=2) + "\n")
