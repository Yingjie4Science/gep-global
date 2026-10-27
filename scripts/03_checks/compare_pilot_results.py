"""Native-grid input/output comparison and diagnostic map for a single-city pilot."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,rasterio,geopandas as gpd
from rasterio.features import geometry_mask
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
p=argparse.ArgumentParser();p.add_argument('pilot',type=Path);a=p.parse_args();d=a.pilot
inputs={}
for local,cloud in [('population_2019','population_gee'),('land_cover_2019','land_cover_gee')]:
 with rasterio.open(d/(local+'.tif')) as r,rasterio.open(d/(cloud+'.tif')) as c:
  assert r.shape==c.shape and r.crs==c.crs and r.transform==c.transform
  x=r.read(1);y=c.read(1);vx=(x>=0) if local.startswith('population') else ~np.isin(x,[0,250]);vy=(y>=0) if local.startswith('population') else ~np.isin(y,[-99999,0,250]);v=vx&vy
  inputs[local]={'same_grid':True,'masks_equal':bool(np.array_equal(vx,vy)),'valid_cells':int(v.sum()),'different_values':int(np.sum(x[v]!=y[v])),'max_absolute_difference':float(np.max(np.abs(x[v]-y[v])))}
with rasterio.open(d/'population_2019.tif') as r:
 pop=r.read(1);transform=r.transform;extent=[r.bounds.left,r.bounds.right,r.bounds.bottom,r.bounds.top]
city=gpd.read_file(d/'city.gpkg');inside=geometry_mask(city.geometry,out_shape=pop.shape,transform=transform,invert=True,all_touched=False)
meta=json.loads((d/'cloud_run_record.json').read_text());cloud_summary=json.loads((d/'cloud_summary.json').read_text())['features'][0]['properties'];local=pd.read_csv(d/'local_outputs/pilot_summary.csv').iloc[0];bridge=pd.read_csv(d/'local_cloud_inputs_outputs/pilot_summary.csv').iloc[0];rate=local.prevalence
comparisons={};rows=[]
with rasterio.open(d/'cloud_outputs.tif') as r:
 for key in ['additional_cases','additional_cases_lower','additional_cases_upper']:
  cloud=r.read(meta['band_names'].index(key)+1)
  with rasterio.open(d/'local_cloud_inputs_outputs'/(key+'_factor.tif')) as f:py=f.read(1).astype(float)*rate
  v=np.isfinite(py)&(cloud!=meta['unmask_fill'])&np.isfinite(cloud)&inside
  assert np.array_equal(np.isfinite(py)&inside,(cloud!=meta['unmask_fill'])&np.isfinite(cloud)&inside)
  diff=np.abs(py[v]-cloud[v]);match=bool(np.allclose(py[v],cloud[v],rtol=2e-6,atol=1e-7))
  assert match,(key,float(diff.max()))
  comparisons[key]={'compared_city_cells':int(v.sum()),'max_absolute_pixel_difference':float(diff.max()),'same_input_local_total':float(bridge[key]),'gee_total':cloud_summary[key],'total_difference':float(bridge[key]-cloud_summary[key]),'pixel_tolerance':'rtol=2e-6,atol=1e-7 case equivalents','passed':match}
  rows.append({'metric':key,'local_zenodo':float(local[key]),'local_same_inputs_as_gee':float(bridge[key]),'gee':cloud_summary[key]})
results={'inputs':inputs,'outputs':comparisons,'scope':'877 city population cells; one 2019 city; not national parity or empirical epidemiological validation','data_difference_percent_point_estimate':float(100*(local.additional_cases/cloud_summary['additional_cases']-1))}
(d/'pilot_comparison.json').write_text(json.dumps(results,indent=2)+'\n');pd.DataFrame(rows).to_csv(d/'pilot_comparison.csv',index=False)
with rasterio.open(d/'land_cover_2019.tif') as r:lc=r.read(1)
with rasterio.open(d/'land_cover_gee.tif') as r:gc=r.read(1)
with rasterio.open(d/'local_outputs/additional_cases_factor.tif') as r:cases=r.read(1)*rate
fig,axes=plt.subplots(1,3,figsize=(13,4.5),constrained_layout=True)
plots=[(np.ma.masked_where(~inside|(pop<0),pop),'Population per cell','viridis',None),(np.ma.masked_where(~inside,lc!=gc),'Land-cover source disagreement',ListedColormap(['#ececec','#d95f02']),(0,1)),(np.ma.masked_where(~inside|~np.isfinite(cases),cases),'Local modeled case equivalents per cell','magma',None)]
for ax,(values,title,cmap,lim) in zip(axes,plots):
 im=ax.imshow(values,extent=extent,origin='upper',cmap=cmap,vmin=lim[0] if lim else None,vmax=lim[1] if lim else None);city.boundary.plot(ax=ax,color='#333333',linewidth=.7);ax.set_title(title,fontsize=10);ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.tick_params(labelsize=8);ax.set_aspect(1/np.cos(np.deg2rad(40.25)))
 cb=fig.colorbar(im,ax=ax,shrink=.75)
 if lim:cb.set_ticks([0,1],labels=['Same','Different'])
fig.suptitle('Fort Morgan, 2019 — technical pilot, not a validated health estimate',fontsize=14)
fig.savefig(d/'pilot_diagnostics.png',dpi=170);plt.close(fig)
print(json.dumps(results,indent=2))
