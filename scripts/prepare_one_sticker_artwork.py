#!/usr/bin/env python3
"""Verify LINE STORE creator/product and render one authentic contact sheet.

Only writes a local image and JSON manifest. GitHub workflow commits them.
No Buffer API use, no cross-repository access, no invented sticker art.
"""
import argparse
import hashlib
import html
import io
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from PIL import Image, ImageOps

AUTHOR = "242076"
MAX_BYTES = 4_000_000


def get(url):
    with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
        content = r.read(MAX_BYTES + 1)
        if r.status != 200 or not content or len(content) > MAX_BYTES:
            raise RuntimeError("REMOTE_RESOURCE_INVALID")
        return content


def source_manifest(sid):
    product_url = f"https://store.line.me/stickershop/product/{sid}/ja"
    page = get(product_url).decode("utf-8")
    if f"/stickershop/author/{AUTHOR}/ja" not in page or "購入する" not in page:
        raise RuntimeError("AUTHOR_OR_SALE_NOT_VERIFIED")
    title_match = re.search(r'data-test="sticker-name-title">(.*?)</', page)
    if not title_match:
        raise RuntimeError("TITLE_NOT_FOUND")
    preview = [json.loads(html.unescape(s)) for s in re.findall(r"data-preview='(.*?)'", page, re.S)]
    urls = [p["staticUrl"] for p in preview if "/v1/sticker/" in str(p.get("staticUrl", ""))]
    if len(urls) not in (8, 16, 24, 32, 40) or len(urls) != len(set(urls)):
        raise RuntimeError("COUNT_OR_ORDER_UNVERIFIED")
    for url in urls:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != "stickershop.line-scdn.net":
            raise RuntimeError("SOURCE_HOST_INVALID")
    return {"sticker_id": sid, "author_id": AUTHOR,
            "title": html.unescape(title_match.group(1)),
            "count": len(urls), "product_url": product_url,
            "official_sources": urls}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sticker-id", required=True)
    p.add_argument("--date", required=True, help="YYYYMMDD in JST")
    args = p.parse_args()
    if not re.fullmatch(r"\d{7,12}", args.sticker_id) or not re.fullmatch(r"\d{8}", args.date):
        raise SystemExit("INVALID_INPUT")
    m = source_manifest(args.sticker_id)
    images = []
    hashes = []
    for url in m["official_sources"]:
        blob = get(url)
        hashes.append(hashlib.sha256(blob).hexdigest())
        with Image.open(io.BytesIO(blob)) as source:
            source.load()
            if not 50 <= source.width <= 3000 or not 50 <= source.height <= 3000:
                raise RuntimeError("DIMENSIONS_INVALID")
            images.append(source.convert("RGBA"))
    sheet = Image.new("RGB", (1600, (len(images) // 4) * 350), "white")
    for i, image in enumerate(images):
        fitted = ImageOps.contain(image, (360, 310), Image.Resampling.LANCZOS)
        x = (i % 4) * 400 + (400 - fitted.width) // 2
        y = (i // 4) * 350 + (350 - fitted.height) // 2
        sheet.paste(fitted, (x, y), fitted)
    out = Path(f"stamps/daily-{args.date}-{args.sticker_id}.jpg")
    manifest = Path(f"stamps/manifests/daily-{args.date}-{args.sticker_id}.json")
    if out.exists() or manifest.exists():
        raise RuntimeError("ALREADY_EXISTS_NO_OVERWRITE")
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    sheet.save(buf, "JPEG", quality=93, subsampling=0, optimize=True)
    raw = buf.getvalue()
    m["image_sha256"] = hashlib.sha256(raw).hexdigest()
    m["official_image_sha256"] = hashes
    m["main_image_url"] = m["official_sources"][0]
    m["main_image_sha256"] = hashes[0]
    m["image_path"] = str(out)
    m["status"] = "ARTWORK_READY_NOT_BUFFER_RESERVED"
    out.write_bytes(raw)
    manifest.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with Image.open(out) as verified:
        verified.load()
        if verified.format != "JPEG" or verified.size != sheet.size:
            raise RuntimeError("RENDER_READBACK_FAILED")
    print("ARTWORK_READY_NOT_BUFFER_RESERVED")
    print(f"STICKER_ID={m['sticker_id']} COUNT={m['count']}")
    print(f"LOCAL_IMAGE={out} SHA256={m['image_sha256']}")
    print(f"LOCAL_MANIFEST={manifest}")


if __name__ == "__main__":
    main()
