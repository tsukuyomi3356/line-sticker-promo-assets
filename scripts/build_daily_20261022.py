import concurrent.futures
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
    if target.exists():
        return
    build(sticker_id, count, target, "ネタさま")

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(one, PRODUCTS))
