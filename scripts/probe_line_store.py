#!/usr/bin/env python3
"""Read-only experiment: inspect LINE STORE's public sticker image links.
Never writes to GitHub and never contacts Buffer.
"""
import html
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PRODUCT_ID = "37344294"  # author's public 16-sticker product, space-themed
STORE_URL = f"https://store.line.me/stickershop/product/{PRODUCT_ID}/ja"
req = Request(STORE_URL, headers={"User-Agent":"Mozilla/5.0 (compatible; LINEStickerPromoTest/1.0; +https://github.com/tsukuyomi3356/line-sticker-promo-assets)", "Accept-Language":"ja,en;q=0.8"})
try:
    with urlopen(req, timeout=30) as response:
        markup = response.read(2_000_000).decode("utf-8", "replace")
        print(f"LINE_STORE_HTTP={response.status} PAGE_BYTES={len(markup)}")
except HTTPError as exc:
    sys.exit(f"LINE_STORE_READ_FAILED: HTTP {exc.code}")
except (URLError, TimeoutError) as exc:
    sys.exit(f"LINE_STORE_READ_FAILED: {type(exc).__name__}")

page=html.unescape(markup.replace(r"\/", "/"))
# Diagnostic only. Real production extraction will validate the HTML element order,
# image sizes and exact 16/24 original sticker count before creating a collage.
ids = re.findall(r'(?:https?:)?//stickershop\.line-scdn\.net/stickershop/v1/sticker/(\d+)/',page)
unique_ids = list(dict.fromkeys(ids))
print(f"STICKER_IDS_FOUND={len(unique_ids)}")
print("FIRST_STICKER_IDS="+",".join(unique_ids[:8]))
print(f"PAGE_HAS_PRODUCT_ID={PRODUCT_ID in page}")
print(f"PAGE_HAS_AUTHOR_NAME={'ネタさま' in page}")
if len(unique_ids) not in (16, 24, 32, 40):
    print("PROBE_INCOMPLETE: Sticker image links were not confirmed; markup may require a browser renderer.")
else:
    print("PROBE_CANDIDATE_FOUND: Count is plausible; order and image quality still require verification.")
print("READ_ONLY: No image uploaded. No Buffer post was created.")
