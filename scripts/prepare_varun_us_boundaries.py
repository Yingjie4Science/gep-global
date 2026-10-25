"""Select non-Hawaii US polygons from Varun's unchanged prepared GUPPD layer.

Usage: python scripts/prepare_varun_us_boundaries.py DATA_ROOT OUTPUT_GPKG OUTPUT_JSON
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import fiona

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('data_root',type=Path);p.add_argument('output_gpkg',type=Path);p.add_argument('output_json',type=Path)
a=p.parse_args();root=a.data_root
source=root/'raw/collaborator/varun_2026-10/urban_boundaries_2019.gpkg'
q=json.loads((root/'manifests/guppd_us_excluding_hawaii_qc.json').read_text())
exclude=set(q['excluded_hawaii_ids'])
if a.output_gpkg.exists():raise FileExistsError(a.output_gpkg)
a.output_gpkg.parent.mkdir(parents=True,exist_ok=True)
ids=[]
with fiona.open(source) as src:
    with fiona.open(a.output_gpkg,'w',driver='GPKG',layer='varun_us_excluding_hawaii',crs=src.crs,schema=src.schema) as dst:
        for feature in src:
            if feature['properties']['iso3']=='USA' and feature['properties']['id'] not in exclude:
                dst.write(feature)
                ids.append(feature['properties']['id'])
assert len(ids)==3309 and len(ids)==len(set(ids))
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
record={'source':str(source.relative_to(root)),'source_sha256':sha(source),'output':str(a.output_gpkg.relative_to(root)) if a.output_gpkg.is_relative_to(root) else str(a.output_gpkg),'output_sha256':sha(a.output_gpkg),'selection':"iso3 = USA and id not in current GUPPD 25-Hawaii exclusion list; no level filter",'feature_count':len(ids),'levels':dict(collections.Counter(i.split('_')[0] for i in ids)),'source_geometry_changed':False,'excluded_hawaii_ids':sorted(exclude)}
a.output_json.parent.mkdir(parents=True,exist_ok=True);a.output_json.write_text(json.dumps(record,indent=2)+'\n')
print(record['feature_count'],record['levels'],record['output_sha256'])
