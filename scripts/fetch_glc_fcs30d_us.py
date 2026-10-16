#!/usr/bin/env python3
"""Acquire 2019 GLC tiles covering all 50 states and DC, including Alaska/Hawaii.
Conservative envelopes intentionally include neighboring countries/ocean. These
are acquisition extents, not a national mask. Territories are outside this scope.
Uses official ZIP member CRCs; keeps resumable compressed parts and status JSON.
"""
import argparse, binascii, concurrent.futures, json, re, struct, tempfile, time
import urllib.request, zipfile, zlib, hashlib
from pathlib import Path
from fetch_glc_fcs30d_tile import request_bytes, extract_2019

ENVELOPES = [(-125,24,-66,50),(-180,50,-130,72),(170,50,180,72),(-179,18,-154,29)]
def get(url):
    with urllib.request.urlopen(url,timeout=180) as r: return json.load(r)
def index(entry):
    url=entry['links']['self']; size=entry['size']; n=min(size,1024*1024)
    tail=request_bytes(url,size-n,size-1)
    with tempfile.NamedTemporaryFile() as f:
        f.truncate(size); f.seek(size-n); f.write(tail); f.flush()
        with zipfile.ZipFile(f.name) as z: infos=z.infolist()
    rows=[]
    for i in infos:
        m=re.search(r'20002022_([EW])(\d+)N(\d+)_Annual',i.filename)
        if not m: continue
        x=int(m[2])*(-1 if m[1]=='W' else 1); y=int(m[3])
        if not any(x<b[2] and x+5>b[0] and y>b[1] and y-5<b[3] for b in ENVELOPES): continue
        rows.append(dict(member=i.filename,url=url,archive=entry['key'],archive_md5=entry['checksum'],offset=i.header_offset,compressed_size=i.compress_size,size=i.file_size,crc=i.CRC,method=i.compress_type,bounds=[x,y-5,x+5,y]))
    return rows

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
def download(row,root):
    name=Path(row['member']).name
    raw=root/'raw/glc_fcs30d'/name
    out=root/'processed/lulc_2019_us'/name.replace('20002022','2019')
    status=root/'manifests/glc_us_tiles'/(name+'.json'); status.parent.mkdir(parents=True,exist_ok=True)
    if status.exists() and out.exists() and json.loads(status.read_text()).get('status')=='verified': return name+' already verified'
    raw.parent.mkdir(parents=True,exist_ok=True)
    part=raw.with_suffix('.tif.deflate.part')
    try:
        if not raw.exists():
            header=request_bytes(row['url'],row['offset'],row['offset']+29)
            fields=struct.unpack('<4s5H3I2H',header)
            if fields[0]!=b'PK\x03\x04': raise ValueError('Invalid ZIP header')
            start=row['offset']+30+fields[-2]+fields[-1]
            offset=part.stat().st_size if part.exists() else 0
            if offset>row['compressed_size']: raise ValueError('Oversized partial file')
            with part.open('ab') as f:
                while offset<row['compressed_size']:
                    end=min(offset+1024*1024,row['compressed_size'])
                    for attempt in range(5):
                        try: data=request_bytes(row['url'],start+offset,start+end-1); break
                        except Exception:
                            if attempt==4: raise
                            time.sleep(2**attempt)
                    f.write(data); f.flush(); offset=end
            temporary=raw.with_suffix('.tif.incomplete'); crc=0; size=0
            dec=zlib.decompressobj(-15)
            with part.open('rb') as f, temporary.open('wb') as dst:
                for b in iter(lambda:f.read(1024*1024),b''):
                    b=dec.decompress(b) if row['method']==8 else b
                    dst.write(b); crc=binascii.crc32(b,crc); size+=len(b)
            if size!=row['size'] or crc & 0xffffffff != row['crc']: raise ValueError('ZIP CRC/size mismatch')
            temporary.replace(raw); part.unlink()
        crc=0
        with raw.open('rb') as f:
            for b in iter(lambda:f.read(8*1024*1024),b''): crc=binascii.crc32(b,crc)
        if raw.stat().st_size!=row['size'] or crc & 0xffffffff != row['crc']: raise ValueError('Existing raw file fails CRC')
        temp=out.with_suffix('.incomplete.tif'); extract_2019(raw,temp); temp.replace(out)
        import rasterio
        with rasterio.open(out) as ds:
            metadata=dict(crs=str(ds.crs),bounds=list(ds.bounds),shape=list(ds.shape),nodata=ds.nodata)
        status.write_text(json.dumps(dict(**row,status='verified',source_year=2019,source_band=20,raw_sha256=sha(raw),output=str(out.relative_to(root)),output_sha256=sha(out),raster=metadata),indent=2))
        return name+' verified'
    except Exception as e:
        status.write_text(json.dumps(dict(**row,status='failed',error=str(e)),indent=2)); return name+' FAILED '+str(e)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('data_root',type=Path); ap.add_argument('--workers',type=int,default=3); ap.add_argument('--plan-only',action='store_true'); args=ap.parse_args()
    plan=args.data_root/'manifests/glc_us_download_plan.json'; plan.parent.mkdir(parents=True,exist_ok=True)
    if plan.exists(): rows=json.loads(plan.read_text())['tiles']
    else:
        record=get('https://zenodo.org/api/records/15063683')
        entries=[f for f in record['files'] if re.search(r'maps_(W(65|75|85|95|105|115|125|135|145|155|165|175)|E170)-',f['key'])]
        rows=[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            for result in pool.map(index,entries): rows.extend(result)
        plan.write_text(json.dumps(dict(scope='50 states and DC; conservative bounding envelopes; territories excluded',envelopes=ENVELOPES,source='https://zenodo.org/records/15063683',compressed_bytes=sum(r['compressed_size'] for r in rows),tiles=rows),indent=2))
    print(f'Tiles: {len(rows)}; compressed transfer: {sum(r["compressed_size"] for r in rows)/1e9:.2f} GB',flush=True)
    if args.plan_only: return
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(lambda r:download(r,args.data_root),rows): print(result,flush=True)
    print('Finished queue. Inspect individual status files for failures before use.',flush=True)
if __name__=='__main__': main()
