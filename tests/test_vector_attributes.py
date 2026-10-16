import tempfile
import unittest
from pathlib import Path
from osgeo import ogr
from vector_attributes import attributes_by_fid

class FeatureIDTest(unittest.TestCase):
    def test_nonsequential_ids_preserve_attributes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'boundaries.gpkg'
            ds = ogr.GetDriverByName('GPKG').CreateDataSource(str(path))
            layer = ds.CreateLayer('urban', geom_type=ogr.wkbPoint)
            layer.CreateField(ogr.FieldDefn('id', ogr.OFTString))
            for fid, name in [(0, 'first'), (7, 'second'), (42, 'third')]:
                feature = ogr.Feature(layer.GetLayerDefn())
                feature.SetFID(fid); feature.SetField('id', name)
                feature.SetGeometry(ogr.CreateGeometryFromWkt('POINT (0 0)'))
                layer.CreateFeature(feature)
            ds = None
            actual = attributes_by_fid(path)
            self.assertEqual({k:v['id'] for k,v in actual.items()}, {0:'first',7:'second',42:'third'})
if __name__ == '__main__': unittest.main()
