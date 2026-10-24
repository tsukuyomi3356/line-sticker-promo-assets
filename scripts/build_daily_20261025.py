import concurrent.futures
import hashlib
import json
from pathlib import Path
from make_line_contact_sheet import build

PRODUCTS = (
    ('37447246',16),('37444789',16),('37431926',16),('37431943',24),
    ('37431941',24),('37431938',24),('37431918',16),('37431917',16),
    ('37431905',16),('37397712',16),
)

def one(product):
    sticker_id, count = product
    target = Path("stamps") / f"daily-20261025-{sticker_id}.jpg"
    if not target.exists():
        build(sticker_id, count, target, "ネタさま")

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(one, PRODUCTS))

entries = []
for sticker_id, count in PRODUCTS:
    target = Path("stamps") / f"daily-20261025-{sticker_id}.jpg"
    entries.append({
        "sticker_id": sticker_id,
        "count": count,
        "path": str(target),
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "size": target.stat().st_size,
    })
manifest = Path("manifests/daily-20261025.json")
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps({"date": "2026-10-25", "products": entries}, ensure_ascii=False, indent=2) + "\n")
