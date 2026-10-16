// Proposed replacement lookup; shared reference script NOT yet verified.
// Sources and decisions: docs/DATA_SOURCES_AND_PREPROCESSING.md.
// Run in an Earth Engine-enabled Cloud Project. First export DE, review it,
// then set STATES=ALL_STATES. No export has been executed by this repository.
var ALL_STATES = 'AL AK AZ AR CA CO CT DE DC FL GA ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split(' ');
var STATES = ['DE']; // Pilot only; Hawaii and territories intentionally excluded.
var YEAR = 2019;
var MIN_OBSERVATIONS = 3; // Proposed QC threshold; inspect coverage sensitivity.
var SCALE = 30;
var CRS = 'EPSG:6933'; // Equal-area analysis grid, explicit for all reductions.
var GLC = 'projects/sat-io/open-datasets/GLC-FCS30D/annual';
var LABELS = {
  "10": "Rainfed cropland",
  "11": "Herbaceous cover cropland",
  "12": "Tree or shrub cover (Orchard) cropland",
  "20": "Irrigated cropland",
  "51": "Open evergreen broadleaved forest",
  "52": "Closed evergreen broadleaved forest",
  "61": "Open deciduous broadleaved forest (0.15<fc<0.4)",
  "62": "Closed deciduous broadleaved forest (fc>0.4)",
  "71": "Open evergreen needle-leaved forest (0.15< fc <0.4)",
  "72": "Closed evergreen needle-leaved forest (fc >0.4)",
  "81": "Open deciduous needle-leaved forest (0.15< fc <0.4)",
  "82": "Closed deciduous needle-leaved forest (fc >0.4)",
  "91": "Open mixed leaf forest (broadleaved and needle-leaved)",
  "92": "Closed mixed leaf forest (broadleaved and needle-leaved)",
  "120": "Shrubland",
  "121": "Evergreen shrubland",
  "122": "Deciduous shrubland",
  "130": "Grassland",
  "140": "Lichens and mosses",
  "150": "Sparse vegetation (fc<0.15)",
  "152": "Sparse shrubland (fc<0.15)",
  "153": "Sparse herbaceous (fc<0.15)",
  "181": "Swamp",
  "182": "Marsh",
  "183": "Flooded flat",
  "184": "Saline",
  "185": "Mangrove",
  "186": "Salt marsh",
  "187": "Tidal flat",
  "190": "Impervious surfaces",
  "200": "Bare areas",
  "201": "Consolidated bare areas",
  "202": "Unconsolidated bare areas",
  "210": "Water body",
  "220": "Permanent ice and snow"
};
var CODES = Object.keys(LABELS).map(Number);
var states = ee.FeatureCollection('TIGER/2018/States');
var annual = ee.ImageCollection(GLC);
print('GLC asset bands (verify b20 before export)', annual.first().bandNames());

function ndvi(image) {
  // Collection 2 surface reflectance scaling; no legacy Collection 1 scale.
  var qa = image.select('QA_PIXEL');
  var clear = qa.bitwiseAnd(63).eq(0); // fill/cloud/cirrus/shadow/snow bits 0-5
  var unsaturated = image.select('QA_RADSAT').eq(0);
  var red = image.select('SR_B4').multiply(0.0000275).add(-0.2);
  var nir = image.select('SR_B5').multiply(0.0000275).add(-0.2);
  var denominator = nir.add(red);
  var valid = clear.and(unsaturated).and(red.gte(0)).and(nir.gte(0)).and(denominator.gt(0));
  // Explicit ratio preserves valid negative NDVI; water is not masked by QA bit 7.
  return nir.subtract(red).divide(denominator).rename('ndvi')
    .updateMask(valid).copyProperties(image, ['system:time_start']);
}

STATES.forEach(function(state) {
  var region = states.filter(ee.Filter.eq('STUSPS', state)).geometry();
  var lc = annual.filterBounds(region).sort('system:index').select('b20').mosaic().rename('lc_code');
  lc = lc.updateMask(lc.neq(0).and(lc.neq(250)));
  var observations = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
    .filterBounds(region).filterDate('2019-01-01', '2020-01-01').map(ndvi);
  var n = observations.count().rename('n_obs');
  var composite = observations.median().updateMask(n.gte(MIN_OBSERVATIONS));
  var valid = composite.mask().unmask(0);
  var area = ee.Image.pixelArea();
  // Sums allow correct pooling across states; never average state means equally.
  var stack = composite.unmask(0).multiply(area).rename('ndvi_area')
    .addBands(composite.unmask(0).pow(2).multiply(area).rename('ndvi2_area'))
    .addBands(valid.multiply(area).rename('valid_area'))
    .addBands(area.rename('class_area'))
    .addBands(valid.rename('valid_cells'))
    .addBands(n.unmask(0).multiply(valid).multiply(area).rename('nobs_area'))
    .addBands(lc).updateMask(lc.mask());
  var sums = stack.reduceRegion({
    reducer: ee.Reducer.sum().repeat(6).group({groupField:6, groupName:'lc_code'}),
    geometry: region, crs: CRS, scale: SCALE, maxPixels:1e13, tileScale:4
  });
  var groups = ee.List(sums.get('groups', ee.List([])));
  var byCode = ee.Dictionary.fromLists(groups.map(function(g) {
    return ee.Number(ee.Dictionary(g).get('lc_code')).format('%d');
  }), groups.map(function(g) { return ee.Dictionary(g).get('sum'); }));
  var rows = ee.FeatureCollection(CODES.map(function(code) {
    var v = ee.List(byCode.get(String(code), ee.List.repeat(0, 6)));
    var sum = ee.Number(v.get(0)); var square = ee.Number(v.get(1));
    var available = ee.Number(v.get(2)); var total = ee.Number(v.get(3));
    var mean = sum.divide(available.max(1));
    return ee.Feature(null, {
      state:state, lc_code:code, lc_desc:LABELS[String(code)],
      lc_ndvi:ee.Algorithms.If(available.gt(0),mean,null),
      ndvi_sd:ee.Algorithms.If(available.gt(0),square.divide(available.max(1)).subtract(mean.pow(2)).max(0).sqrt(),null),
      ndvi_area_sum:sum, ndvi2_area_sum:square, valid_area_m2:available,
      class_area_m2:total, valid_cell_count:v.get(4), nobs_area_sum:v.get(5),
      valid_area_fraction:ee.Algorithms.If(total.gt(0),available.divide(total.max(1)),null),
      year:YEAR, temporal_statistic:'annual median of valid 2019 Landsat 8 NDVI',
      spatial_statistic:'area-weighted mean of annual pixel medians',
      minimum_observations:MIN_OBSERVATIONS, analysis_crs:CRS, analysis_scale_m:SCALE,
      glc_asset:GLC, glc_band:'b20', landsat_asset:'LANDSAT/LC08/C02/T1_L2',
      status:ee.Algorithms.If(available.gt(0),'candidate_requires_review','no_valid_observations')
    });
  }));
  Export.table.toDrive({collection:rows,description:'glc_ndvi_2019_'+state,
    fileNamePrefix:'glc_ndvi_2019_'+state,fileFormat:'CSV'});
});
// Class SD describes spatial variation, not a confidence interval. No missing
// class receives a zero NDVI. Region-specific or urban-only lookups should be
// compared before adopting this US-wide proxy. Export/review class-area coverage
// against TIGER/GUPPD as GLC missing coverage is not measured by NDVI valid fraction.
