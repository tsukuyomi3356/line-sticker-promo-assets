#!/usr/bin/env python3
"""Build an original-sticker contact sheet from a public LINE STORE product.

Read the public page, validate author/ID/count, fetch each original sticker
image in page order, compose a single contact sheet and save it locally.
No Buffer post is created. No private credentials are needed.
"""
import argparse
import hashlib
import html
import io
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image, ImageOps, ImageDraw

USER_AGENT = "Mozilla/5.0 (compatible; LINEStickerPromoImageTest/1.0)"
CDN_PREFIX = "stickershop.line-scdn.net/stickershop/v1/sticker/"

def read_url(url, max_bytes=4_000_000):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language":"ja,en;q=0.8"})
    try:
        with urlopen(req, timeout=25) as response:
            if response.status != 200:
                raise ValueError(f"HTTP {response.status} for {url}")
            content = response.read(max_bytes + 1)
            if len(content) > max_bytes:
                raise ValueError("Downloaded content exceeds safety limit")
            return content
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not fetch {url} ({type(exc).__name__})") from exc

def sticker_url_candidates(page, sticker_id):
    expression = re.compile(
        r"((?:https?:)?//" + re.escape(CDN_PREFIX)
        + re.escape(sticker_id) + r"/[^\s<>\x22\x27\\)]+)", re.I
    )
    # Source is HTML; src can contain URL-encoded query parameters.
    seen = set()
    candidates = []
    for value in expression.findall(page):
        candidate = ("https:" + value if value.startswith("//") else value)
        candidate = candidate.rstrip(";,")
        if candidate not in seen:
            seen.add(candidate)
            candidates.append(candidate)
    # The known LINE CDN standard path is used only if page-provided URL fails.
    candidates.append(f"https://{CDN_PREFIX}{sticker_id}/android/sticker.png")
    candidates.sort(key=lambda u: (
        0 if "/android/sticker.png" in u else
        1 if "/iPhone/sticker.png" in u else
        2 if "sticker.png" in u else
        3,
        len(u)
    ))
    return list(dict.fromkeys(candidates))

def fetch_sticker(page, sticker_id):
    errors=[]
    for url in sticker_url_candidates(page, sticker_id):
        try:
            data = read_url(url, 3_000_000)
            image = Image.open(io.BytesIO(data))
            image.load()
            if image.format not in ("PNG", "WEBP", "JPEG"):
                raise ValueError("Unsupported file format")
            if min(image.size) < 80:
                raise ValueError(f"Image unexpectedly small: {image.size}")
            return image.convert("RGBA")
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
    raise RuntimeError(f"Sticker {sticker_id} could not be downloaded from the LINE CDN; attempts={len(errors)}")

def build(product_id, expected_count, output, author):
    product_url = f"https://store.line.me/stickershop/product/{product_id}/ja"
    page = html.unescape(read_url(product_url, 2_000_000).decode("utf-8","replace")).replace("\\/", "/")
    ids = list(dict.fromkeys(re.findall(
        r"(?:https?:)?//" + re.escape(CDN_PREFIX) + r"(\d+)/", page
    )))
    print(f"PRODUCT_ID={product_id} PAGE_STICKER_COUNT={len(ids)} EXPECTED_COUNT={expected_count}", flush=True)
    if product_id not in page or author not in page:
        raise RuntimeError("Product ID or creator name not verified; refusing to build")
    if len(ids) != expected_count:
        raise RuntimeError("Sticker count mismatch; refusing incomplete or unrelated contact sheet")
    if expected_count not in (16,24):
        raise RuntimeError("Only 16/24 sticker sets are supported in this test")
    stickers=[]
    for idx, image_id in enumerate(ids, 1):
        img = fetch_sticker(page, image_id)
        stickers.append(img)
        print(f"DOWNLOADED {idx:02d}/{expected_count} ID={image_id} SIZE={img.width}x{img.height}",flush=True)
    cols=4
    rows=expected_count//cols
    cell_w,cell_h=404,350
    gap=10
    margin=16
    width=margin*2+cols*cell_w+(cols-1)*gap
    height=margin*2+rows*cell_h+(rows-1)*gap
    canvas=Image.new("RGB",(width,height),"white")
    draw=ImageDraw.Draw(canvas)
    for i, sticker in enumerate(stickers):
        c,r=i%cols,i//cols
        left=margin+c*(cell_w+gap)
        top=margin+r*(cell_h+gap)
        draw.rounded_rectangle((left,top,left+cell_w-1,top+cell_h-1),radius=10,fill=(248,249,250))
        scaled=ImageOps.contain(sticker,(cell_w-14,cell_h-14),Image.Resampling.LANCZOS)
        x=left+(cell_w-scaled.width)//2
        y=top+(cell_h-scaled.height)//2
        canvas.paste(scaled,(x,y),scaled)
    if output.exists():
        raise RuntimeError(f"Refusing to overwrite pre-existing image: {output}")
    output.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(output,format="JPEG",quality=92,optimize=True,subsampling=0)
    with Image.open(output) as check:
        check.load()
        if check.format!="JPEG" or check.size!=(width,height):
            raise RuntimeError("Generated image failed quality verification")
    digest=hashlib.sha256(output.read_bytes()).hexdigest()[:16]
    print(f"CONTACT_SHEET_OK COUNT={expected_count} PATH={output} SIZE={width}x{height} SHA256_PREFIX={digest}",flush=True)
    print("NO_BUFFER_POST: this test only fetches/composes/publishes an image asset",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--product-id",default="37344294")
    p.add_argument("--count",type=int,default=16)
    p.add_argument("--author",default="ネタさま")
    p.add_argument("--output",default="stamps/test-37344294-16.jpg")
    a=p.parse_args()
    try:
        build(a.product_id,a.count,Path(a.output),a.author)
    except Exception as exc:
        print(f"IMAGE_TEST_FAILED: {exc}",file=sys.stderr,flush=True)
        sys.exit(1)
