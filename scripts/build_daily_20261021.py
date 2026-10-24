import concurrent.futures
from pathlib import Path
from make_line_contact_sheet import build
PRODUCTS=[["37431926",16],["37431943",24],["37431941",24],["37431938",24],["37431918",16],["37431917",16],["37397712",16],["37344316",16],["37344293",16],["37130802",16]]
def one(p):
    sid,n=p
    target=Path("stamps")/("daily-20261021-"+sid+".jpg")
    if target.exists(): return
    build(sid,n,target,"ネタさま")
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(one,PRODUCTS))
