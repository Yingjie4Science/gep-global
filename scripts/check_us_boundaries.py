"""Read-only geometry overlap audit; boundary slivers are reported, not repaired."""
import argparse,json
from pathlib import Path
import fiona
from shapely.geometry import shape
from shapely.strtree import STRtree
from pyproj import Geod
ap=argparse.ArgumentParser();ap.add_argument('data_root',type=Path);args=ap.parse_args()
source=args.data_root/'processed/guppd_us_excluding_hawaii.gpkg'
with fiona.open(source) as f: rows=list(f)
geoms=[shape(f['geometry']) for f in rows];tree=STRtree(geoms);geod=Geod(ellps='WGS84');pairs=[]
for i,g in enumerate(geoms):
    for j in tree.query(g,predicate='intersects'):
        if j<=i:continue
        overlap=g.intersection(geoms[j])
        if overlap.area<=1e-12:continue
        area=abs(geod.geometry_area_perimeter(overlap)[0])
        pairs.append(dict(id_a=rows[i]['properties']['id'],id_b=rows[j]['properties']['id'],area_m2=area))
report=dict(feature_count=len(rows),overlap_pairs=pairs,method='STRtree intersections; positive area above 1e-12 square degrees; WGS84 ellipsoidal area',note='No repairs applied; area and population-grid cell assignment need review before national aggregation.')
out=args.data_root/'manifests/guppd_us_overlap_qc.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
