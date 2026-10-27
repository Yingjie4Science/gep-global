"""Compare 2020 GHS-SMOD 21+ with 2019 GUPPD in two US urban regions.

Run from the repository root with the snapp geospatial environment:
    python scripts/03_checks/compare_smod_guppd_cities.py

The public Earth Engine image is downloaded once per city into ignored raw data.
Area uses a 1 km EPSG:5070 grid and cell-centre polygon membership. Population
uses the same 2019 WorldPop 100 m source for both masks; GHS-SMOD is nearest-
neighbour resampled to that grid. The comparison domain is a 10 km buffer of
one GUPPD polygon. It is a bounded coverage illustration, not Chiara's full run.
"""
from __future__ import annotations

import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import matplotlib.patheffects as path_effects
import numpy as np
import rasterio
from rasterio.features import geometry_mask, shapes
from rasterio.warp import Resampling, reproject
from rasterio.windows import from_bounds
from shapely.geometry import box, mapping, shape

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data'
EVIDENCE = ROOT / 'docs' / 'evidence'
CROPS = DATA / 'raw' / 'ghs_smod' / '2020_two_city_crops'
IMAGE_ID = 'JRC/GHSL/P2023A/GHS_SMOD_V2-0/2020'
BUFFER_M = 10_000
URBAN_CODES = (21, 22, 23, 30)
CITIES = (
    ('San Francisco Bay Area', 'san_francisco', '30_12257'),
    ('Minneapolis–Saint Paul', 'minneapolis', '30_12427'),
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def download_crop(path: Path, region_bounds_5070) -> None:
    import ee
    ee.Initialize(project='natcap-gep')
    region = gpd.GeoSeries([box(*region_bounds_5070)], crs=5070).to_crs(4326).iloc[0]
    image = ee.Image(IMAGE_ID).select('smod_code')
    url = image.getDownloadURL({
        'region': region.__geo_interface__, 'crs': 'EPSG:5070',
        'scale': 1000, 'format': 'GEO_TIFF',
    })
    payload = urllib.request.urlopen(url, timeout=120).read()
    if payload[:2] == b'PK':
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = [name for name in archive.namelist() if name.endswith('.tif')]
            if len(names) != 1:
                raise ValueError(f'Expected one TIFF in GEE download: {names}')
            payload = archive.read(names[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def population_counts(pop_path: Path, smod, smod_src, polygon, buffer_geom):
    with rasterio.open(pop_path) as pop_src:
        polygon_geo = gpd.GeoSeries([polygon], crs=5070).to_crs(pop_src.crs).iloc[0]
        buffer_geo = gpd.GeoSeries([buffer_geom], crs=5070).to_crs(pop_src.crs).iloc[0]
        window = from_bounds(*buffer_geo.bounds, transform=pop_src.transform)
        window = window.round_offsets().round_lengths()
        pop = pop_src.read(1, window=window)
        transform = pop_src.window_transform(window)
        smod_on_pop = np.full(pop.shape, -200, dtype=np.int16)
        reproject(
            smod, smod_on_pop, src_transform=smod_src.transform,
            src_crs=smod_src.crs, src_nodata=smod_src.nodata,
            dst_transform=transform, dst_crs=pop_src.crs,
            dst_nodata=-200, resampling=Resampling.nearest,
        )
        in_buffer = geometry_mask([mapping(buffer_geo)], out_shape=pop.shape,
                                  transform=transform, invert=True)
        in_guppd = geometry_mask([mapping(polygon_geo)], out_shape=pop.shape,
                                 transform=transform, invert=True) & in_buffer
        in_smod = np.isin(smod_on_pop, URBAN_CODES) & in_buffer
        valid = np.isfinite(pop) & (pop > 0) & (pop != pop_src.nodata)
        return {
            'guppd': float(pop[in_guppd & valid].sum(dtype='float64')),
            'smod_21_plus': float(pop[in_smod & valid].sum(dtype='float64')),
            'both': float(pop[in_guppd & in_smod & valid].sum(dtype='float64')),
            'smod_only': float(pop[in_smod & ~in_guppd & valid].sum(dtype='float64')),
            'guppd_only': float(pop[in_guppd & ~in_smod & valid].sum(dtype='float64')),
        }


def plot_city(path: Path, label: str, smod, src, polygon, in_buffer, in_guppd, in_smod,
              area, population):
    class_image = np.full(smod.shape, 0, dtype=np.uint8)
    for code, idx in ((21, 1), (22, 2), (23, 3), (30, 4)):
        class_image[(smod == code) & in_buffer] = idx
    class_image[~in_buffer] = 5
    overlap = np.zeros(smod.shape, dtype=np.uint8)
    overlap[in_guppd & in_smod] = 1
    overlap[in_smod & ~in_guppd] = 2
    overlap[in_guppd & ~in_smod] = 3
    overlap[~in_buffer] = 4
    extent = (src.bounds.left, src.bounds.right,
              src.bounds.bottom, src.bounds.top)
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 7.2))
    fig.subplots_adjust(left=0.03, right=0.97, top=0.87, bottom=0.27, wspace=0.07)
    class_cmap = ListedColormap(['#e8ecef', '#e8d65a', '#db9a51', '#a66555', '#c94e4e', '#ffffff'])
    overlap_cmap = ListedColormap(['#e8ecef', '#227b80', '#ed9a37', '#7d5eaf', '#ffffff'])
    axes[0].imshow(class_image, cmap=class_cmap, vmin=0, vmax=5,
                   interpolation='nearest', extent=extent, origin='upper')
    axes[1].imshow(overlap, cmap=overlap_cmap, vmin=0, vmax=4,
                   interpolation='nearest', extent=extent, origin='upper')
    # Vectorize the selected SMOD cells so its outline follows actual 1 km cell
    # edges. This is the mask clipped to the 10 km display window, not a named city.
    smod_polygons = [shape(geometry) for geometry, value in shapes(
        in_smod.astype('uint8'), mask=in_smod, transform=src.transform)
        if value == 1]
    smod_boundary = gpd.GeoSeries(smod_polygons, crs=5070).boundary
    guppd_boundary = gpd.GeoSeries([polygon], crs=5070).boundary
    for ax in axes:
        smod_boundary.plot(ax=ax, color='#c2185b', linewidth=1.25,
                           linestyle='--', zorder=4)
        ax.collections[-1].set_path_effects([
            path_effects.Stroke(linewidth=2.6, foreground='white'),
            path_effects.Normal(),
        ])
        guppd_boundary.plot(ax=ax, color='#17212b', linewidth=1.3, zorder=5)
        ax.set_xlim(src.bounds.left, src.bounds.right)
        ax.set_ylim(src.bounds.bottom, src.bounds.top)
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
    axes[0].set_title('GHS-SMOD settlement classes', fontsize=13, weight='bold')
    axes[1].set_title('Urban coverage overlap', fontsize=13, weight='bold')
    axes[0].legend(handles=[Patch(facecolor=c, label=t) for c, t in [
        ('#e8d65a', '21 suburban/peri-urban'), ('#db9a51', '22 semi-dense'),
        ('#a66555', '23 dense'), ('#c94e4e', '30 urban centre')]],
        loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=2,
        fontsize=8.4, frameon=False)
    axes[1].legend(handles=[Patch(facecolor=c, label=t) for c, t in [
        ('#227b80', 'Both'), ('#ed9a37', 'SMOD only'),
        ('#7d5eaf', 'GUPPD only')]], loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=2,
        fontsize=8.4, frameon=False)
    fig.suptitle(label, fontsize=17, weight='bold')
    fig.legend(handles=[
        Line2D([0], [0], color='#17212b', linewidth=1.5,
               label='GUPPD polygon boundary'),
        Line2D([0], [0], color='#c2185b', linewidth=1.7, linestyle='--',
               label='GHS-SMOD 21+ cell boundary'),
    ], loc='lower center', bbox_to_anchor=(0.5, 0.15), ncol=2,
        frameon=False, fontsize=9.2)
    fig.text(0.5, 0.10,
             f"GUPPD + 10 km buffer: GUPPD {area['guppd']:,.0f} km² / "
             f"{population['guppd']/1e6:.2f}m people; SMOD 21+ "
             f"{area['smod_21_plus']:,.0f} km² / {population['smod_21_plus']/1e6:.2f}m people",
             ha='center', fontsize=10.5, weight='bold')
    fig.text(0.5, 0.055,
             '2020 GHS-SMOD • 2019 GUPPD • 2019 WorldPop • 1 km area grid • '
             'SMOD outline is clipped at window edge • not municipal limits',
             ha='center', fontsize=8.5, color='#495463')
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def main():
    guppd_path = DATA / 'processed' / 'guppd_us_contiguous.gpkg'
    pop_path = DATA / 'raw' / 'worldpop' / 'usa_pop_2019_CN_100m_R2025A_v1.tif'
    guppd = gpd.read_file(guppd_path).set_index('id')
    results = {'source': IMAGE_ID, 'source_year': 2020,
               'area_grid': 'EPSG:5070, 1000 m; cell-centre membership',
               'comparison_buffer_m': BUFFER_M,
               'population': '2019 WorldPop constrained R2025A v1, native 100 m; '
                             'SMOD nearest-neighbour sampled at population cells',
               'input_sha256': {'guppd': sha256(guppd_path),
                                'worldpop': sha256(pop_path)}, 'cities': {}}
    for label, slug, city_id in CITIES:
        polygon = gpd.GeoSeries([guppd.loc[city_id].geometry],
                                crs=guppd.crs).to_crs(5070).iloc[0]
        buffer_geom = polygon.buffer(BUFFER_M)
        crop_path = CROPS / f'{slug}_smod_2020_1km_5070.tif'
        if not crop_path.exists():
            download_crop(crop_path, buffer_geom.bounds)
        with rasterio.open(crop_path) as src:
            smod = src.read(1)
            if src.crs.to_epsg() != 5070 or abs(src.res[0] - 1000) > 1:
                raise ValueError(f'Unexpected SMOD crop grid: {crop_path}')
            in_buffer = geometry_mask([mapping(buffer_geom)], out_shape=smod.shape,
                                      transform=src.transform, invert=True)
            in_guppd = geometry_mask([mapping(polygon)], out_shape=smod.shape,
                                     transform=src.transform, invert=True) & in_buffer
            in_smod = np.isin(smod, URBAN_CODES) & in_buffer
            cell_km2 = abs(src.transform.a * src.transform.e) / 1e6
            area = {key: int(mask.sum()) * cell_km2 for key, mask in {
                'guppd': in_guppd, 'smod_21_plus': in_smod,
                'both': in_guppd & in_smod,
                'smod_only': in_smod & ~in_guppd,
                'guppd_only': in_guppd & ~in_smod,
            }.items()}
            population = population_counts(pop_path, smod, src, polygon, buffer_geom)
            figure = EVIDENCE / 'figures' / f'smod_guppd_{slug}.png'
            plot_city(figure, label, smod, src, polygon, in_buffer, in_guppd,
                      in_smod, area, population)
            results['cities'][slug] = {
                'label': label, 'guppd_id': city_id,
                'guppd_vector_area_km2': polygon.area / 1e6,
                'area_km2': area, 'population_people': population,
                'smod_class_km2_inside_guppd': {
                    str(code): int(((smod == code) & in_guppd).sum()) * cell_km2
                    for code in URBAN_CODES},
                'smod_class_km2_smod_only': {
                    str(code): int(((smod == code) & in_smod & ~in_guppd).sum()) * cell_km2
                    for code in URBAN_CODES},
                'smod_crop_sha256': sha256(crop_path),
                'figure': str(figure.relative_to(ROOT)),
            }
    output = EVIDENCE / 'data' / 'smod_guppd_two_city_summary.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2) + '\n')
    print(output)
    for city in results['cities'].values():
        print(city['label'], city['area_km2'], city['population_people'])


if __name__ == '__main__':
    main()
