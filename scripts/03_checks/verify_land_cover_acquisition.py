"""Verify completed acquisition files against their recorded hashes and 2019 metadata."""
import argparse,hashlib,json
from pathlib import Path
import rasterio

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('data_root',type=Path);p.add_argument('output',type=Path);a=p.parse_args();rows=[]
 plan=json.loads((a.data_root/'manifests/glc_us_download_plan.json').read_text())['tiles']
 for tile in plan:
  name=Path(tile['member']).name;status=a.data_root/'manifests/glc_us_tiles'/(name+'.json');record={'tile':name,'passed':False}
  try:
   m=json.loads(status.read_text());assert m['status']=='verified',m.get('error','Not verified');raw=a.data_root/'raw/glc_fcs30d'/name;out=a.data_root/m['output'];assert sha(raw)==m['raw_sha256'],'Raw hash mismatch';assert sha(out)==m['output_sha256'],'2019 hash mismatch'
   with rasterio.open(raw) as src,rasterio.open(out) as dst:
    assert src.count==23 and dst.count==1 and src.transform==dst.transform and src.crs==dst.crs and src.shape==dst.shape
    # Deterministic beginning, centre and final windows verify band selection.
    import numpy as np
    for y,x in [(0,0),(src.height//2,src.width//2),(src.height-64,src.width-64)]:
     win=rasterio.windows.Window(x,y,min(64,src.width-x),min(64,src.height-y));assert np.array_equal(src.read(20,window=win),dst.read(1,window=win)),'Band20 extraction mismatch'
   record.update(passed=True,raw_sha256=m['raw_sha256'],output_sha256=m['output_sha256'])
  except Exception as e:record['error']=str(e)
  rows.append(record)
  if len(rows)%10==0:print('Audited',len(rows),'tiles',flush=True)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'planned_tiles':len(rows),'passed_tiles':sum(r['passed'] for r in rows),'complete':all(r['passed'] for r in rows),'tiles':rows},indent=2)+'\n')
 print('Passed',sum(r['passed'] for r in rows),'of',len(rows),flush=True)
if __name__=='__main__':main()
