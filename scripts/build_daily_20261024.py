import concurrent.futures
import hashlib
import json
from pathlib import Path
from make_line_contact_sheet import build

PRODUCTS = (('37500693',24),('37492877',16),('37492850',24),('37492839',16),('37492838',16),('37477492',16),('37478017',24),('37472071',16),('37447258',16),('37447255',24))

def one(product):
    sticker_id, count = product
    target = Path("stamps") / f"daily-20261024-{sticker_id}.jpg"
    if not target.exists():
        build(sticker_id, count, target, "ネタさま")

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(one, PRODUCTS))

entries = []
for sticker_id, count in PRODUCTS:
    target = Path("stamps") / f"daily-20261024-{sticker_id}.jpg"
    entries.append({
        "sticker_id": sticker_id,
        "count": count,
        "path": str(target),
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "size": target.stat().st_size,
    })
manifest = Path("manifests/daily-20261024.json")
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps({"date": "2026-10-24", "products": entries}, ensure_ascii=False, indent=2) + "\n")
