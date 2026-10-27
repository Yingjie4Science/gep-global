"""Read actual driver feature IDs, preserving gaps and zero-based identifiers."""
from osgeo import ogr

def attributes_by_fid(path):
    vector = ogr.Open(str(path))
    if vector is None:
        raise ValueError(f"Cannot open processing boundary: {path}")
    layer = vector.GetLayer(0)
    rows = {feature.GetFID(): feature.items() for feature in layer}
    vector = None
    return rows
