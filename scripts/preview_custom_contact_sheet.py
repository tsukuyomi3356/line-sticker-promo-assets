#!/usr/bin/env python3
"""Build a verified LINE STORE sheet for review, without publishing."""
import argparse,hashlib,json,re,sys
from pathlib import Path
from make_line_contact_sheet import build

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--product-id",required=True)
    p.add_argument("--count",required=True,type=int)
    args=p.parse_args()
    if not re.fullmatch(r"[0-9]{7,12}",args.product_id):sys.exit("INVALID_PRODUCT_ID")
    if args.count not in (16,24):
        sys.exit("UNSUPPORTED_COUNT: 8-image validation is still pending")
    folder=Path("review-artifacts")
    folder.mkdir(exist_ok=True)
    path=folder/("review-"+args.product_id+"-"+str(args.count)+".jpg")
    build(args.product_id,args.count,path,"ネタさま")
    checksum=hashlib.sha256(path.read_bytes()).hexdigest()
    (folder/"manifest.json").write_text(json.dumps(
      {"product_id":args.product_id,"count":args.count,"sha256":checksum,
       "review_only":True,"published":False},ensure_ascii=False,indent=2),encoding="utf-8")
    print("PREVIEW_READY="+str(path))
    print("NO_PUBLIC_UPLOAD_OR_BUFFER_POST")
if __name__=="__main__":main()
